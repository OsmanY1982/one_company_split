# `iqra/core/chat_engine.py`

> 路径：`iqra/core/chat_engine.py` | 行数：706


---


```python
# -*- coding: utf-8 -*-
import json
import os
import re as _re_module
from typing import Optional, Iterator, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from .llm_backend import (BaseLLMBackend, LLMResponse, ToolCall, ProviderConfig, create_backend)
from .tool_registry import ToolRegistry
from .memory_store import MemoryStore
from .smart_memory_adapter import SmartMemoryStore
from .iqra_logging import logger
from .rag_context import RAGContextInjector

class ChatEngine(QObject):
    on_tool_start = pyqtSignal(str, dict)
    on_tool_result = pyqtSignal(str, bool, str)
    MAX_TOOL_ROUNDS = 5
    MAX_CONTEXT_MSGS = 40
    _PROMPT_TOOLS_MARKER = '<!--PROMPT_TOOLS_INJECTED-->'

    def __init__(self, backend, registry=None, system_prompt='', skill_loader=None,
                 memory_store=None, auto_save=True, session_id='default'):
        super().__init__()
        self.backend = backend
        self.registry = registry or ToolRegistry()
        self.system_prompt = system_prompt
        self.skill_loader = skill_loader
        if isinstance(memory_store, SmartMemoryStore):
            self.memory_store = memory_store
            self.smart_memory = memory_store.smart
        elif memory_store is not None:
            self.memory_store = memory_store
            self.smart_memory = None
        else:
            self.memory_store = None
            self.smart_memory = None
        self.auto_save = auto_save
        self.session_id = session_id
        self.obs = None  # ObservableBridge，由 agent_bridge 注入
        self.messages = []
        if self.memory_store:
            self.messages = self.memory_store.load_session(self.session_id)
        self._save_counter = 0
        self.on_thinking = None
        self.initialize_session()
        logger.debug(f'ChatEngine initialized session={session_id} msgs={len(self.messages)}')

    def initialize_session(self) -> None:
        """初始化会话上下文（公开方法，替代原来的私有方法）"""
        if not (self.system_prompt or self.registry.count() > 0 or self.skill_loader):
            return
        parts = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        if self.registry.count() > 0 and not self.system_prompt:
            # 只有在没有外部传入 system_prompt 时才添加默认提示
            tool_names = self.registry.list_tools()
            tool_summary = ', '.join(sorted(tool_names))
            intro = (
                '你是 Iqra，一人公司的全能数字员工。\n'
                '\n'
                '核心规则：\n'
                '1. 永远用工具完成任务，不要只是聊天或给建议\n'
                '2. 读取文件用 read_file，严禁用 execute_shell + cat/osascript；搜索文件用 search_files，严禁用 find/grep\n'
                '3. 用户要求做具体操作时，立刻调用对应工具，不要先解释\n'
                '4. 独立操作并行调用，不要串行等待\n'
                '5. 工具返回结果后，基于结果给出分析或下一步行动\n'
                f'6. 可用工具({len(tool_names)}个): {tool_summary}\n'
                '\n'
                '回复风格：中文、简洁、直接。'
            )
            parts.append(intro)
        # 技能索引（仅列技能名，不注入完整内容以节省 token）
        if self.skill_loader:
            try:
                all_skills = self.skill_loader.list_skills()
                if all_skills:
                    skill_names = sorted([s['name'] for s in all_skills])
                    total = len(skill_names)
                    skills_index = (
                        f"[可用技能索引 - 共 {total} 个]\n"
                        f"{', '.join(skill_names)}\n\n"
                        "💡 需要某个技能的详细内容时，调用 inject_skill(技能名) 即可加载。"
                    )
                    parts.append(skills_index)
            except Exception:
                pass
        if self.memory_store:
            personalized = self.memory_store.get_personalized_context()
            if personalized:
                parts.append(f'[User Preferences]\n{personalized}')
        if parts:
            new_sys = {'role': 'system', 'content': '\n\n'.join(parts)}
            if self.messages and self.messages[0]['role'] == 'system':
                self.messages[0] = new_sys
            else:
                self.messages.insert(0, new_sys)
        self._trim_context()

    def _trim_context(self) -> int:
        """
        智能上下文裁剪（LLM 摘要优先 + 机械裁剪兜底）

        策略：
          1. 未溢出 → 不裁剪
          2. LLM 摘要压缩中间轮次（质量优先）
          3. LLM 失败/不可用 → 回退机械裁剪
        """
        total = len(self.messages)
        if total <= self.MAX_CONTEXT_MSGS:
            return 0

        sys_msg = self.messages[0] if (self.messages and self.messages[0]['role'] == 'system') else None
        keep_recent = max(30, self.MAX_CONTEXT_MSGS // 2)
        sys_slot = 1 if sys_msg else 0
        middle = self.messages[sys_slot:-keep_recent]
        recent = self.messages[-keep_recent:]

        # ── 优先 LLM 摘要压缩（有中间消息 + backend 可用时） ──
        if middle and self.backend:
            summary = self._llm_summarize_context(middle)
            if summary:
                result = []
                if sys_msg:
                    result.append(sys_msg)
                result.append({"role": "user", "content": f"[上下文摘要]\n{summary}"})
                result.extend(recent)
                trimmed = total - len(result)
                self.messages = result
                logger.info("LLM 上下文压缩: %d 条 → %d 条 (%d 字摘要)", total, len(result), len(summary))
                return trimmed

        # ── 回退：机械裁剪 ──
        total_slot = self.MAX_CONTEXT_MSGS
        kept_middle = []
        for msg in middle:
            content = msg.get("content", "")
            if isinstance(content, str):
                if ("error" in content.lower() or "失败" in content
                        or "exception" in content.lower()):
                    kept_middle.append(msg)
                    continue
                if msg.get("role") == "tool" and len(content) > 500:
                    kept_middle.append(msg)
                    continue
                if msg.get("role") == "user":
                    kept_middle.append(msg)
                    continue

        remaining_slots = total_slot - sys_slot - keep_recent
        if remaining_slots > 0 and kept_middle:
            kept_middle = kept_middle[-remaining_slots:]

        result = []
        if sys_msg:
            result.append(sys_msg)
        result.extend(kept_middle)
        result.extend(recent)
        trimmed = total - len(result)
        self.messages = result
        return trimmed

    def _llm_summarize_context(self, middle_messages: list) -> Optional[str]:
        """
        调用 LLM 将中间段对话压缩为结构化摘要。

        只在上下文严重溢出时调用（>20 条中间消息），
        摘要内容包含：用户需求变化、关键决策点、已执行操作、
        工具调用结果要点、遇到的错误及处理方式。

        Returns:
            摘要字符串，失败时返回 None（调用方应回退机械裁剪）
        """
        if not middle_messages:
            return None

        # 压缩消息：取关键轮次（跳过纯 tool 结果超过 2KB 的大输出，降低 prompt 开销）
        compact_msgs = []
        for msg in middle_messages:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 2048:
                content = content[:2048] + "...[截断]"
            compact_msgs.append({"role": msg["role"], "content": content})

        # 构建摘要提示词
        msg_json = json.dumps(compact_msgs, ensure_ascii=False, indent=2)
        prompt = f"""你是一个上下文压缩器。以下是一段对话的中间轮次（非开头非结尾），请将其压缩为结构化摘要。

要求：
1. 列出用户提出的**所有需求**（含已放弃或修改的需求）
2. 列出 AI 执行的**关键操作**（工具调用 + 结果要点，每条 ≤ 30 字）
3. 列出**重要决策与转折点**（如"用户推翻方案A"、"改为用 Python 处理"）
4. 列出**未解决的错误或阻塞**（如仍存在的问题）
5. 禁止包含系统提示词、人格描述、问候语
6. 输出纯中文，使用 Markdown 无序列表格式，总长度 ≤ 800 字

对话轮次（共 {len(middle_messages)} 条）：
{msg_json}

请输出压缩后的结构化摘要："""

        try:
            # 使用极简参数调用 LLM（max_tokens=1024，temperature=0）
            response = self.backend.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0,
            )
            summary = response.content.strip()
            if summary and len(summary) > 20:
                logger.info("LLM 上下文压缩: %d 条 → %d 字摘要", len(middle_messages), len(summary))
                return summary
            return None
        except Exception as e:
            logger.warning("LLM 摘要压缩失败: %s，回退机械裁剪", e)
            return None

    def save(self) -> bool:
        if self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)
            return True
        return False

    def inject_context(self, text: str) -> None:
        if self.messages and self.messages[0]['role'] == 'system':
            self.messages[0]['content'] += f'\n\n{text}'
        else:
            self.messages.insert(0, {'role': 'system', 'content': text})

    def inject_skill(self, skill_name: str) -> bool:
        if not self.skill_loader:
            return False
        ctx = self.skill_loader.get_skill_context(skill_name, include_full=True)
        if ctx and not ctx.startswith('❌'):
            self.inject_context(ctx)
            return True
        return False

    def inject_relevant_skills(self, user_query: str, max_count: int = 5) -> int:
        """根据用户输入自动注入最相关的技能（节省 token 的按需加载）"""
        if not self.skill_loader:
            return 0
        # 先移除之前注入的技能上下文，防止 system prompt 无限增长
        if self.messages and self.messages[0]['role'] == 'system':
            content = self.messages[0]['content']
            # 移除之前注入的技能块（以 ## 📖 开头）
            import re
            content = re.sub(r'\n## 📖 技能：.*?(?=\n## |\Z)', '', content, flags=re.DOTALL)
            self.messages[0]['content'] = content
        skills = self.skill_loader.auto_select_skills_for_query(user_query, max_count=max_count)
        injected = 0
        for s in skills:
            name = s.get('name', '')
            ctx = self.skill_loader.get_skill_context(name, include_full=False)
            if ctx and not ctx.startswith('❌'):
                self.inject_context(ctx)
                injected += 1
        return injected

    def inject_workspace_context(self, user_message: str) -> bool:
        """自动注入工作区代码上下文 + 项目规则（HybridRetriever: BM25初筛 + Embedding精排）"""
        injector = RAGContextInjector()
        if not injector.enabled or not injector.has_project:
            return False
        try:
            # ── 可观测性：语义搜索步骤追踪 ──
            ss_step = -1
            t0 = 0.0
            if self.obs:
                ss_step = self.obs.semantic_search_begin(query=user_message)
                t0 = __import__('time').time()

            context = injector.get_context(user_message, max_chars=4000, top_k=5, use_semantic=True)
            result_count = len(context.split('\n---\n')) if context else 0

            if self.obs and ss_step >= 0:
                elapsed = (__import__('time').time() - t0) * 1000
                self.obs.semantic_search_end(ss_step, result_count=result_count, elapsed_ms=elapsed)

            # 注入项目规则（IQRA.md — 对标 CLAUDE.md）
            rules = injector.get_project_rules()
            if rules:
                context = rules + "\n\n" + context if context else rules

            if not context:
                return False
            # 清除旧的 workspace 上下文块，然后注入新的
            if self.messages and self.messages[0]['role'] == 'system':
                content = self.messages[0]['content']
                content = _re_module.sub(
                    r'\n<workspace_context>.*?</workspace_context>\n', '', content, flags=_re_module.DOTALL
                )
                self.messages[0]['content'] = content
            self.inject_context(f'<workspace_context>\n{context}\n</workspace_context>')
            return True
        except Exception as e:
            logger.warning(f'Workspace context injection failed: {e}')
            return False

    def refresh_skills(self) -> int:
        if not self.skill_loader:
            return 0
        all_skills = self.skill_loader.list_skills()
        count = len(all_skills)
        if count > 0 and self.messages and self.messages[0]['role'] == 'system':
            skill_names = sorted([s['name'] for s in all_skills])
            skills_index = (
                f"[可用技能索引 - 共 {count} 个]\n"
                f"{', '.join(skill_names)}\n\n"
                "💡 需要某个技能的详细内容时，调用 inject_skill(技能名) 即可加载。"
            )
            base = self.messages[0]['content']
            marker = '[可用技能索引'
            if marker in base:
                base = base[:base.index(marker)]
            self.messages[0]['content'] = base.strip() + '\n\n' + skills_index
        return count

    def _prepare_context(self, user_message: str) -> tuple:
        """准备本轮对话上下文：技能注入、工作区 RAG、工具列表、强制工具判断。
        Returns (tools_list_or_None, force_tools_bool)"""
        if self.skill_loader:
            try:
                self.inject_relevant_skills(user_message, max_count=5)
            except Exception as e:
                logger.warning(f'Skill auto-inject failed: {e}')
        self.inject_workspace_context(user_message)
        tools = self.registry.to_openai_tools() if self.registry.count() > 0 else None
        force_tools = self._should_force_tools(user_message)
        return tools, force_tools

    def chat(self, user_message: str) -> str:
        logger.debug(f'chat() called msg_len={len(user_message)}')
        if self.memory_store:
            self.memory_store.on_turn_start(turn_number=len(self.messages), message=user_message)
        if self.obs:
            self.obs.trace_begin(session_id=self.session_id, user_message=user_message)
        self.messages.append({'role': 'user', 'content': user_message})
        self._trim_context()
        tools, force_tools = self._prepare_context(user_message)
        use_prompt_tools = False  # True: LLM 不支持 native function calling，用 prompt 方式驱动工具
        
        for _ in range(self.MAX_TOOL_ROUNDS):
            try:
                if use_prompt_tools:
                    response = self.backend.chat(self.messages, None)
                elif force_tools and tools:
                    response = self.backend.chat(self.messages, tools, tool_choice="required")
                else:
                    response = self.backend.chat(self.messages, tools)
            except Exception as e:
                logger.error(f'LLM API failed: {e}', exc_info=True)
                self._remove_prompt_tools()
                self.messages.append({'role': 'assistant', 'content': f'Sorry, AI service unavailable: {e}'})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                return f'Sorry, AI service unavailable: {e}'

            # ── Prompt-based 工具调用路径 ──
            if use_prompt_tools:
                visible_text, parsed_tc = self._parse_prompt_tool_calls(response.content or '')
                if parsed_tc:
                    # LLM 调用了工具：执行并追加到消息历史
                    self.messages.append({'role': 'assistant', 'content': visible_text or None})
                    exec_results = self._execute_parsed_tool_calls(parsed_tc)
                    for ptc, result in exec_results:
                        tool_msg = {'role': 'tool', 'tool_call_id': ptc['id'],
                            'content': json.dumps(result, ensure_ascii=False)}
                        self.messages.append(tool_msg)
                    continue  # 下一轮让 LLM 看到工具结果后继续
                # 没有工具调用，最终回复
                final_text = visible_text or response.content or ''
                self.messages.append({'role': 'assistant', 'content': final_text})
                self._remove_prompt_tools()
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                return final_text

            # ── 原生 Function Calling 路径 ──
            if not response.tool_calls:
                # 本地模型可能不支持 native function calling：降级到 prompt-based
                if force_tools and tools:
                    use_prompt_tools = True
                    self._inject_prompt_tools(tools)
                    continue
                assistant_msg = response.content or ''
                self.messages.append({'role': 'assistant', 'content': assistant_msg})
                if self.auto_save and self.memory_store:
                    self.memory_store.save_session(self.messages, self.session_id)
                if self.obs:
                    self.obs.trace_end()
                return assistant_msg
            assistant_msg = {'role': 'assistant', 'content': None, 'tool_calls': []}
            for tc in response.tool_calls:
                self.on_tool_start.emit(tc.name, tc.arguments)
                try:
                    result = self.registry.execute(tc)
                except Exception as e:
                    logger.error(f'Tool failed {tc.name}: {e}', exc_info=True)
                    result = {'success': False, 'error': f'Tool error: {e}'}
                self.on_tool_result.emit(tc.name, result['success'],
                    str(result.get('result', result.get('error', '')))[:200])
                try:
                    assistant_msg['tool_calls'].append({'id': tc.id, 'type': 'function',
                        'function': {'name': tc.name, 'arguments': json.dumps(tc.arguments, ensure_ascii=False)}})
                except (TypeError, ValueError) as e:
                    logger.warning(f'Serialization failed: {e}')
                    continue
                try:
                    tool_msg = {'role': 'tool', 'tool_call_id': tc.id,
                        'content': json.dumps(result, ensure_ascii=False)}
                    self.messages.append(tool_msg)
                except (TypeError, ValueError) as e:
                    logger.warning(f'Result serialization failed: {e}')
                    self.messages.append({'role': 'tool', 'tool_call_id': tc.id,
                        'content': json.dumps({'success': False, 'error': 'Result cannot be serialized'}, ensure_ascii=False)})
            self.messages.append(assistant_msg)
        self._remove_prompt_tools()
        if self.auto_save and self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)
        if self.obs:
            self.obs.trace_end()
        return 'Sorry, processing encountered a loop. Please try a different approach.'

    # ── Prompt-based Tool Calling (本地模型降级) ──

    def _generate_prompt_tools_desc(self, tools: list) -> str:
        """为 prompt-based tool calling 生成工具描述和 XML 格式指令"""
        tool_descs = []
        for t in tools:
            func = t.get('function', {})
            name = func.get('name', '?')
            desc = func.get('description', '')
            params = func.get('parameters', {})
            tool_descs.append(f'- {name}: {desc}')
            for pname, pinfo in params.get('properties', {}).items():
                required = ' [必填]' if pname in params.get('required', []) else ''
                tool_descs.append(f'    {pname}{required}: {pinfo.get("description", "")}')
        desc_block = '\n'.join(tool_descs)
        return (
            f'你需要使用工具来完成任务。不要只是聊天或给建议，必须调用工具执行操作。\n'
            f'要调用工具，在回复中插入以下格式的 XML 块：\n'
            f'\n'
            f'<tool>\n'
            f'{{"name": "工具名", "arguments": {{"参数名": "参数值"}}}}\n'
            f'</tool>\n'
            f'\n'
            f'一次可以调用多个工具，使用多个 <tool> 块。不要在 <tool> 块之外输出工具调用指令。\n'
            f'\n'
            f'可用工具：\n'
            f'{desc_block}\n'
            f'\n'
            f'{self._PROMPT_TOOLS_MARKER}'
        )

    def _parse_prompt_tool_calls(self, text: str) -> tuple:
        """从 LLM 回复中解析 <tool> XML 块，返回 (visible_text, tool_calls_list)。
        tool_calls_list 中每个元素为 {'id': str, 'name': str, 'arguments': dict}"""
        import re as _re
        tool_calls = []
        def _replace_tool(match):
            content = match.group(1).strip()
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for item in parsed:
                    tc_id = f'ptc_{len(tool_calls):04d}'
                    tool_calls.append({
                        'id': tc_id,
                        'name': item.get('name', ''),
                        'arguments': item.get('arguments', {}),
                    })
            except json.JSONDecodeError:
                pass
            return ''
        visible = _re.sub(r'<tool>\s*(.*?)\s*</tool>', _replace_tool, text, flags=_re.DOTALL).strip()
        return visible, tool_calls

    def _inject_prompt_tools(self, tools: list) -> None:
        """在消息列表末尾注入 prompt-based 工具描述（带标记，可追踪移除）"""
        desc = self._generate_prompt_tools_desc(tools)
        self.messages.append({'role': 'system', 'content': desc})

    def _remove_prompt_tools(self) -> int:
        """移除所有带 _PROMPT_TOOLS_MARKER 标记的系统消息，返回移除数量"""
        removed = 0
        self.messages = [
            m for m in self.messages
            if not (m['role'] == 'system' and self._PROMPT_TOOLS_MARKER in m.get('content', ''))
        ]
        # 实际 removed count 由前后长度差算出
        return removed

    def _execute_parsed_tool_calls(self, parsed_tool_calls: list) -> list:
        """执行解析出的工具调用，返回 (assistant_msg_parts, tool_result_msgs) 的元组列表。
        同时发射 on_tool_start / on_tool_result 信号。"""
        results = []
        for ptc in parsed_tool_calls:
            self.on_tool_start.emit(ptc['name'], ptc['arguments'])
            tc = ToolCall(id=ptc['id'], name=ptc['name'], arguments=ptc['arguments'])
            try:
                result = self.registry.execute(tc)
            except Exception as e:
                logger.error(f'Tool failed {ptc["name"]}: {e}', exc_info=True)
                result = {'success': False, 'error': f'Tool error: {e}'}
            self.on_tool_result.emit(
                ptc['name'],
                result.get('success', False),
                str(result.get('result', result.get('error', '')))[:200],
            )
            results.append((ptc, result))
        return results

    def _should_force_tools(self, user_message: str) -> bool:
        """判断是否应该强制使用工具。跳过纯能力询问（以"吗？"/"吗"/"？"结尾的寒暄句）"""
        msg_stripped = user_message.strip()
        # 纯元问题（"你能...吗？""你支持...?"）不强制工具，交给 LLM 自然决策
        if msg_stripped.endswith(('吗？', '吗', '？')) or msg_stripped.endswith('?'):
            return False
        force_keywords = [
            '执行', '运行', '调用', '使用', '打开', '关闭', '创建', '删除',
            '读取', '写入', '修改', '搜索', '查询', '分析', '计算',
            'file', 'read', 'write', 'execute', 'run', 'search', 'query',
            'create', 'delete', 'open', 'close', 'modify', 'analyze',
        ]
        msg_lower = user_message.lower()
        return any(kw in msg_lower for kw in force_keywords)

    def chat_stream(self, user_message: str) -> Iterator[str]:
        logger.debug(f'chat_stream() called msg_len={len(user_message)} tools={self.registry.count()}')
        if self.memory_store:
            self.memory_store.on_turn_start(turn_number=len(self.messages), message=user_message)
        if self.obs:
            self.obs.trace_begin(session_id=self.session_id, user_message=user_message)
        self.messages.append({'role': 'user', 'content': user_message})
        self._trim_context()
        self._save_counter += 1
        tools, force_tools = self._prepare_context(user_message)
        use_prompt_tools = False  # True: LLM 不支持 native function calling
        
        for round_idx in range(self.MAX_TOOL_ROUNDS):
            if self.on_thinking:
                self.on_thinking()
            if tools:
                try:
                    import datetime, sys
                    if use_prompt_tools:
                        check_response = self.backend.chat(self.messages, None)
                    elif force_tools:
                        check_response = self.backend.chat(self.messages, tools, tool_choice="required")
                    else:
                        check_response = self.backend.chat(self.messages, tools)
                    print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] ChatEngine.chat_stream round={round_idx} backend.chat() returned — content_len={len(check_response.content or '')}, tool_calls={'YES' if check_response.tool_calls else 'NO'}, prompt_mode={use_prompt_tools}", flush=True)
                except Exception as e:
                    logger.error(f'LLM API failed: {e}', exc_info=True)
                    self._remove_prompt_tools()
                    self._maybe_save()
                    if self.obs:
                        self.obs.trace_end()
                    yield '\nSorry, AI service unavailable: {}\n'.format(e)
                    return

                # ── Prompt-based 工具调用路径 ──
                if use_prompt_tools:
                    visible_text, parsed_tc = self._parse_prompt_tool_calls(check_response.content or '')
                    if parsed_tc:
                        # LLM 调用了工具
                        self.messages.append({'role': 'assistant', 'content': visible_text or None})
                        yield (visible_text + '\n') if visible_text else '\n'
                        exec_results = self._execute_parsed_tool_calls(parsed_tc)
                        for ptc, result in exec_results:
                            self.on_tool_start.emit(ptc['name'], ptc['arguments'])
                            status = 'OK' if result.get('success') else 'Failed'
                            yield f'\n[{ptc["name"]}: {status}]\n'
                            tool_msg = {'role': 'tool', 'tool_call_id': ptc['id'],
                                'content': json.dumps(result, ensure_ascii=False)}
                            self.messages.append(tool_msg)
                        continue  # 下一轮让 LLM 看到工具结果后继续
                    # 没有工具调用，最终回复
                    final_text = visible_text or check_response.content or ''
                    self.messages.append({'role': 'assistant', 'content': final_text})
                    self._remove_prompt_tools()
                    self._maybe_save()
                    if self.obs:
                        self.obs.trace_end()
                    yield final_text
                    if check_response.usage:
                        yield json.dumps({'usage': check_response.usage}, ensure_ascii=False)
                    return

                # ── 原生 Function Calling 路径 ──
                if check_response.tool_calls:
                    for tc in check_response.tool_calls:
                        self.on_tool_start.emit(tc.name, tc.arguments)
                        yield f'\n[Calling tool: {tc.name}...]\n'
                        try:
                            result = self.registry.execute(tc)
                        except Exception as e:
                            logger.error(f'Tool failed {tc.name}: {e}', exc_info=True)
                            result = {'success': False, 'error': f'Tool error: {e}'}
                        self.on_tool_result.emit(tc.name, result['success'],
                            str(result.get('result', result.get('error', '')))[:200])
                        status = 'OK' if result['success'] else 'Failed'
                        yield f'[{tc.name}: {status}]\n'
                        try:
                            assistant_msg = {'role': 'assistant', 'content': None, 'tool_calls': [{
                                'id': tc.id, 'type': 'function',
                                'function': {'name': tc.name, 'arguments': json.dumps(tc.arguments, ensure_ascii=False)}
                            }]}
                            tool_msg = {'role': 'tool', 'tool_call_id': tc.id,
                                'content': json.dumps(result, ensure_ascii=False)}
                            self.messages.append(assistant_msg)
                            self.messages.append(tool_msg)
                        except (TypeError, ValueError) as e:
                            logger.warning(f'Serialization failed: {e}')
                    continue
                # 没有 tool_calls：如果不是强制工具模式则直接返回，否则降级到 prompt-based
                if not force_tools:
                    return_text = check_response.content or ''
                    self.messages.append({'role': 'assistant', 'content': return_text})
                    self._maybe_save()
                    if self.obs:
                        self.obs.trace_end()
                    yield return_text
                    if check_response.usage:
                        yield json.dumps({'usage': check_response.usage}, ensure_ascii=False)
                    return
                # 降级到 prompt-based
                use_prompt_tools = True
                self._inject_prompt_tools(tools)
                continue
            try:
                accumulated = ''
                last_usage = {}
                for chunk in self.backend.chat_stream(self.messages):
                    if chunk.content:
                        accumulated += chunk.content
                        yield chunk.content
                    if hasattr(chunk, 'usage') and chunk.usage:
                        last_usage = chunk.usage
                # Fallback: streaming 返回空时降级到非 streaming 调用
                if not accumulated:
                    try:
                        fallback_resp = self.backend.chat(self.messages, tools)
                        if fallback_resp.content:
                            accumulated = fallback_resp.content
                            yield accumulated
                            if fallback_resp.usage:
                                last_usage = fallback_resp.usage
                    except Exception:
                        pass
                self.messages.append({'role': 'assistant', 'content': accumulated})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                if last_usage:
                    yield json.dumps({'usage': last_usage}, ensure_ascii=False)
                return
            except Exception as e:
                logger.error(f'Streaming failed: {e}', exc_info=True)
                self.messages.append({'role': 'assistant', 'content': f'Sorry, AI service unavailable: {e}'})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                yield f'\nSorry, AI service unavailable: {e}\n'
                return
        self._remove_prompt_tools()
        self._maybe_save()
        self._trim_context()
        yield '\n[Max processing rounds reached, please simplify your question]'

    def _maybe_save(self):
        if self.auto_save and self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)
        # 每轮结束后自动同步到记忆插件
        if self.memory_store and hasattr(self.memory_store, 'sync_all'):
            try:
                self.memory_store.sync_all()
            except Exception:
                pass

    def reset(self) -> None:
        if self.auto_save and self.memory_store:
            # 会话结束前持久化语义搜索索引
            self._persist_semantic_index()
            self.memory_store.on_session_end(self.session_id)
            self.memory_store.save_session([], self.session_id)
        self.messages = []
        self.initialize_session()

    def _persist_semantic_index(self) -> None:
        """会话结束前，将 FAISS 语义索引持久化到 SmartMemoryStore"""
        try:
            injector = RAGContextInjector()
            injector.save_index_to_memory(self.memory_store, index_name="default")
        except Exception:
            pass

    def get_history(self) -> list[dict]:
        return list(self.messages)

    def message_count(self) -> int:
        return len(self.messages)

```
