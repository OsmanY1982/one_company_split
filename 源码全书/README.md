# 一人公司 · 宇宙版 — 源码全书
> 自动生成于 2026-06-29 08:34
> 共 1406 个模块，每个 `.py` 文件独立为一个文档

---

## 目录结构

```
.
├── _archive/
│   ├── core/
│   │   ├── shapes/
│   │   │   ├── classic_20260614_184255_598.py
│   │   │   ├── gas_giant_20260614_184255_426.py
│   │   │   ├── ice_giant_20260614_184255_207.py
│   │   │   ├── lava_planet_20260614_184255_101.py
│   │   │   └── mars_20260614_184255_257.py
│   │   ├── data_20260619_111935_141.py
│   │   └── planet_painter_20260614_151048_302.py
│   ├── iqra/
│   │   └── core/
│   │       ├── shapes/
│   │       │   ├── classic_20260614_184255_598.py
│   │       │   ├── gas_giant_20260614_184255_426.py
│   │       │   ├── ice_giant_20260614_184255_207.py
│   │       │   ├── lava_planet_20260614_184255_101.py
│   │       │   └── mars_20260614_184255_257.py
│   │       ├── data_20260619_111935_141.py
│   │       └── planet_painter_20260614_151048_302.py
│   ├── management-system/
│   │   └── core/
│   │       ├── shapes/
│   │       │   ├── classic_20260614_184255_598.py
│   │       │   ├── gas_giant_20260614_184255_426.py
│   │       │   ├── ice_giant_20260614_184255_207.py
│   │       │   ├── lava_planet_20260614_184255_101.py
│   │       │   └── mars_20260614_184255_257.py
│   │       ├── data_20260619_111935_141.py
│   │       └── planet_painter_20260614_151048_302.py
│   └── planetarium/
│       └── core/
│           └── shapes/
│               ├── classic_20260614_184255_598.py
│               ├── gas_giant_20260614_184255_426.py
│               ├── ice_giant_20260614_184255_207.py
│               ├── lava_planet_20260614_184255_101.py
│               └── mars_20260614_184255_257.py
├── config/
│   ├── __init__.py
│   └── supabase_config.py
├── core/
│   ├── _deprecated/
│   │   ├── cloud_sync_v2.py
│   │   ├── sync_optimized.py
│   │   └── triple_sync.py
│   ├── config/
│   │   └── supabase_config.py
│   ├── data/
│   │   ├── enhanced/
│   │   ├── metrics/
│   ├── iqra/
│   │   └── data/
│   ├── knowledge_base/
│   ├── log/
│   ├── modules/
│   │   ├── account/
│   │   │   ├── __init__.py
│   │   │   ├── account_activation.py
│   │   │   ├── account_update.py
│   │   │   ├── activation_service.py
│   │   │   ├── activation_stats.py
│   │   │   ├── activation_stats_service.py
│   │   │   └── license_local.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin_activation.py
│   │   │   ├── admin_backup.py
│   │   │   ├── admin_data.py
│   │   │   ├── admin_data_mgmt.py
│   │   │   ├── admin_finance.py
│   │   │   ├── admin_log.py
│   │   │   ├── admin_orders.py
│   │   │   ├── admin_product.py
│   │   │   ├── admin_service.py
│   │   │   ├── admin_settings.py
│   │   │   ├── admin_staff.py
│   │   │   ├── admin_strategy.py
│   │   │   ├── admin_user.py
│   │   │   ├── admin_window.py
│   │   │   ├── cascade_delete.py
│   │   │   └── strategy_dao.py
│   │   ├── astronomy/
│   │   │   ├── solar_system/
│   │   │   │   ├── planets/
│   │   │   │   │   ├── callisto/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── ceres/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── earth/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── enceladus/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── eris/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── europa/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── ganymede/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── haumea/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── io/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── jupiter/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── makemake/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── mars/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── mercury/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── moon/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── neptune/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── pluto/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── saturn/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── sun/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── titan/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── uranus/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── venus/
│   │   │   │   │   │   ├── knowledge/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── _base.py
│   │   │   │   ├── window/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _colors.py
│   │   │   │   │   ├── _hud.py
│   │   │   │   │   └── _window.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ad_player.py
│   │   │   │   ├── data.py
│   │   │   │   ├── renderer.py
│   │   │   │   └── window.py
│   │   │   ├── star_catalog/
│   │   │   │   ├── data_entries/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _collections.py
│   │   │   │   │   ├── _dwarf_planets.py
│   │   │   │   │   ├── _moons_earth.py
│   │   │   │   │   ├── _moons_jupiter.py
│   │   │   │   │   ├── _moons_neptune.py
│   │   │   │   │   ├── _moons_pluto.py
│   │   │   │   │   ├── _moons_saturn.py
│   │   │   │   │   ├── _moons_uranus.py
│   │   │   │   │   ├── _planets.py
│   │   │   │   │   └── _sun.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── catalog.py
│   │   │   │   ├── data_entries.py
│   │   │   │   ├── detail.py
│   │   │   │   ├── encyclopedia.py
│   │   │   │   └── voice.py
│   │   │   ├── __init__.py
│   │   │   └── hub.py
│   │   ├── auth/
│   │   │   ├── dao/
│   │   │   │   ├── session_dao.py
│   │   │   │   └── user_dao.py
│   │   │   ├── model_config_panel/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _constants.py
│   │   │   │   ├── _dialog.py
│   │   │   │   ├── _panel_config.py
│   │   │   │   ├── _panel_custom.py
│   │   │   │   ├── _panel_local.py
│   │   │   │   ├── _panel_preset.py
│   │   │   │   ├── _panel_ui.py
│   │   │   │   └── _workers.py
│   │   │   ├── service/
│   │   │   │   ├── cloud_api.py
│   │   │   │   ├── session_service.py
│   │   │   │   └── sync_auth_service.py
│   │   │   ├── __init__.py
│   │   │   ├── activation_gate.py
│   │   │   ├── admin_login_dialog.py
│   │   │   ├── auth_service.py
│   │   │   ├── auth_service_membership.py
│   │   │   ├── auth_service_sync.py
│   │   │   ├── change_password_dialog.py
│   │   │   ├── connect_window.py
│   │   │   ├── login_window.py
│   │   │   ├── model_setup_window.py
│   │   │   ├── register_window.py
│   │   │   ├── select_mode_window.py
│   │   │   ├── upgrade_window.py
│   │   ├── business/
│   │   │   ├── __init__.py
│   │   │   ├── business_window.py
│   │   │   ├── customer_service.py
│   │   │   ├── customer_window.py
│   │   │   ├── finance_service.py
│   │   │   ├── finance_window.py
│   │   │   ├── order_service.py
│   │   │   ├── order_window.py
│   │   │   ├── product_service.py
│   │   │   └── product_window.py
│   │   ├── common/
│   │   │   ├── advanced_filter_window.py
│   │   │   └── custom_field_window.py
│   │   ├── dashboard/
│   │   │   ├── dashboard_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _account_tools.py
│   │   │   │   ├── _module_navigator.py
│   │   │   │   ├── _module_window.py
│   │   │   │   ├── _planets.py
│   │   │   │   ├── _renderer.py
│   │   │   │   └── _ui.py
│   │   │   └── dashboard_window.py
│   │   ├── data_center/
│   │   │   ├── __init__.py
│   │   │   ├── bi_window.py
│   │   │   ├── chart_window.py
│   │   │   ├── data_window.py
│   │   │   ├── report_service.py
│   │   │   ├── report_service_v2.py
│   │   │   ├── report_window.py
│   │   │   └── smart_report_window.py
│   │   ├── i18n/
│   │   │   └── i18n_window.py
│   │   ├── industry/
│   │   │   ├── industry_adapter.py
│   │   │   ├── industry_config.py
│   │   │   ├── industry_report.py
│   │   │   └── industry_window.py
│   │   ├── intelligence/
│   │   │   ├── _chat_dialog/
│   │   │   │   ├── __init__.py
│   │   │   │   └── _dialog.py
│   │   │   ├── agent_bridge_tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _code_tools.py
│   │   │   │   ├── _file_tools.py
│   │   │   │   ├── _legacy_tools.py
│   │   │   │   ├── _system_tools.py
│   │   │   │   ├── _task_tools.py
│   │   │   │   └── _web_tools.py
│   │   │   ├── ai_chat_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _chat_stream.py
│   │   │   │   ├── _file_upload.py
│   │   │   │   ├── _misc.py
│   │   │   │   ├── _model_selector.py
│   │   │   │   ├── _session.py
│   │   │   │   ├── _ui.py
│   │   │   │   └── _voice.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   └── llm_backend.py
│   │   │   ├── data/
│   │   │   │   ├── learning/
│   │   │   │   └── reflections/
│   │   │   ├── enhanced/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _enhanced_base.py
│   │   │   │   ├── _enhanced_files_mixin.py
│   │   │   │   ├── _enhanced_storage_mixin.py
│   │   │   │   ├── _enhanced_system_mixin.py
│   │   │   │   ├── _enhanced_web_mixin.py
│   │   │   │   └── enhanced_tools.py
│   │   │   ├── iqra_floating_planet/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _chat_mixin.py
│   │   │   │   ├── _core.py
│   │   │   │   ├── _exit_mixin.py
│   │   │   │   ├── _modules_mixin.py
│   │   │   │   ├── floating_planet_anim_mixin.py
│   │   │   │   ├── floating_planet_draw_mixin.py
│   │   │   │   └── floating_planet_menu_mixin.py
│   │   │   ├── marketing_tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _core.py
│   │   │   │   └── _registration.py
│   │   │   ├── quick_tools_panel/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _api_config.py
│   │   │   │   └── _quick_tools.py
│   │   │   ├── solar_system_data/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _catalog.py
│   │   │   │   ├── _core.py
│   │   │   │   └── _data.py
│   │   │   ├── text_editor/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _core.py
│   │   │   │   ├── _crypto.py
│   │   │   │   └── _note_tab.py
│   │   │   ├── workflow_engine/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _engine.py
│   │   │   │   └── _models.py
│   │   │   ├── __init__.py
│   │   │   ├── _ai_shared.py
│   │   │   ├── _ai_widgets.py
│   │   │   ├── _ai_widgets_anomaly.py
│   │   │   ├── _ai_widgets_business.py
│   │   │   ├── _ai_widgets_core.py
│   │   │   ├── _ai_widgets_recommendation.py
│   │   │   ├── _ai_widgets_visualization.py
│   │   │   ├── _ai_widgets_workflow.py
│   │   │   ├── _compat.py
│   │   │   ├── _model_manager.py
│   │   │   ├── _model_manager_download.py
│   │   │   ├── _model_manager_ollama.py
│   │   │   ├── _navigation_hud.py
│   │   │   ├── _shell_dialogs.py
│   │   │   ├── _stubs.py
│   │   │   ├── account_window.py
│   │   │   ├── agent_bridge.py
│   │   │   ├── agent_bridge_models.py
│   │   │   ├── agent_bridge_workers.py
│   │   │   ├── ai_assistant_window.py
│   │   │   ├── ai_center_window.py
│   │   │   ├── ai_chat_styles.py
│   │   │   ├── ai_chat_window.py
│   │   │   ├── ai_dashboard_window.py
│   │   │   ├── ai_features_ai_dashboard.py
│   │   │   ├── ai_features_customer_ai.py
│   │   │   ├── ai_features_inventory_ai.py
│   │   │   ├── ai_features_pricing_ai.py
│   │   │   ├── ai_features_sales_ai.py
│   │   │   ├── analysis_tools.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── auto_task_executor.py
│   │   │   ├── backup_window.py
│   │   │   ├── batch_text.py
│   │   │   ├── business_ai_assistant.py
│   │   │   ├── business_tools.py
│   │   │   ├── chat_session_manager.py
│   │   │   ├── compress_tool.py
│   │   │   ├── crm_tools.py
│   │   │   ├── data_import_tools.py
│   │   │   ├── data_visualization.py
│   │   │   ├── db_helper.py
│   │   │   ├── download_dialog.py
│   │   │   ├── editor_window.py
│   │   │   ├── enhanced_chat.py
│   │   │   ├── event_trigger.py
│   │   │   ├── file_rename_tools.py
│   │   │   ├── finance_analysis_tools.py
│   │   │   ├── floating_planet.py
│   │   │   ├── floating_planet_anim_mixin.py
│   │   │   ├── floating_planet_draw_mixin.py
│   │   │   ├── floating_planet_menu_mixin.py
│   │   │   ├── hr_tools.py
│   │   │   ├── img_converter.py
│   │   │   ├── intelligence_integration.py
│   │   │   ├── intelligence_window.py
│   │   │   ├── inventory_tools.py
│   │   │   ├── iqra_floating_planet.py
│   │   │   ├── json_tools.py
│   │   │   ├── key_manager.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── marketing_tools.py
│   │   │   ├── model_config.py
│   │   │   ├── monitor_dashboard.py
│   │   │   ├── offline_analyzer.py
│   │   │   ├── password_tools.py
│   │   │   ├── performance_monitor.py
│   │   │   ├── predictor_window.py
│   │   │   ├── quick_actions.py
│   │   │   ├── quick_tools_panel.py
│   │   │   ├── rag_injector.py
│   │   │   ├── recommendation_engine.py
│   │   │   ├── report_generator.py
│   │   │   ├── sales_predictor.py
│   │   │   ├── scan_window.py
│   │   │   ├── screen_recorder.py
│   │   │   ├── self_monitor.py
│   │   │   ├── session_context.py
│   │   │   ├── smart_assistant.py
│   │   │   ├── smart_report_tools.py
│   │   │   ├── smart_workflow.py
│   │   │   ├── solar_system_data.py
│   │   │   ├── solar_system_window.py
│   │   │   ├── super_intelligence.py
│   │   │   ├── system_hub_window.py
│   │   │   ├── system_monitor.py
│   │   │   ├── text_editor.py
│   │   │   ├── timestamp_tools.py
│   │   │   ├── tool_registry.py
│   │   │   ├── tools_window.py
│   │   │   ├── usb_scanner.py
│   │   │   ├── vault_window.py
│   │   │   ├── voice_interface.py
│   │   │   ├── whisper_recognizer.py
│   │   │   ├── window_top_tools.py
│   │   │   └── workflow_engine.py
│   │   ├── notification/
│   │   │   └── notification_window.py
│   │   ├── permission/
│   │   │   └── permission_window.py
│   │   ├── personnel/
│   │   │   ├── distribution_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _commissions.py
│   │   │   │   ├── _dashboard.py
│   │   │   │   ├── _links.py
│   │   │   │   ├── _stat_card.py
│   │   │   │   ├── _team.py
│   │   │   │   └── _ui.py
│   │   │   ├── wallet_service/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _address.py
│   │   │   │   ├── _cloud.py
│   │   │   │   ├── _db.py
│   │   │   │   ├── _transactions.py
│   │   │   │   ├── _wallet_crud.py
│   │   │   │   └── _withdrawal_queue.py
│   │   │   ├── wallet_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _address_book.py
│   │   │   │   ├── _batch_ops.py
│   │   │   │   ├── _dashboard_tab.py
│   │   │   │   ├── _dialogs.py
│   │   │   │   ├── _stat_card.py
│   │   │   │   ├── _transactions_tab.py
│   │   │   │   ├── _wallets_tab.py
│   │   │   │   └── _withdrawal_tab.py
│   │   │   ├── __init__.py
│   │   │   ├── distribution_service.py
│   │   │   ├── member_service.py
│   │   │   ├── member_window.py
│   │   │   ├── personnel_window.py
│   │   │   ├── staff_service.py
│   │   │   ├── staff_window.py
│   │   │   └── wallet_window.py
│   │   ├── startup/
│   │   │   └── startup_selector_window.py
│   │   ├── supabase/
│   │   │   ├── __init__.py
│   │   │   ├── _core.py
│   │   │   ├── activation.py
│   │   │   ├── admin_log.py
│   │   │   ├── auth.py
│   │   │   ├── business.py
│   │   │   ├── distribution.py
│   │   │   ├── member.py
│   │   │   ├── updater.py
│   │   │   └── wallet.py
│   │   ├── system/
│   │   │   ├── _archived/
│   │   │   │   ├── activation_window.py
│   │   │   │   ├── base_info_window.py
│   │   │   │   ├── cloud_window.py
│   │   │   │   ├── logs_window.py
│   │   │   │   ├── system_window.py
│   │   │   │   └── update_dialog.py
│   │   │   ├── __init__.py
│   │   │   ├── audit_window.py
│   │   │   ├── base_info_window.py
│   │   │   ├── cloud_model_panel.py
│   │   │   ├── cloud_module.py
│   │   │   ├── cloud_server_window.py
│   │   │   ├── cloud_window.py
│   │   │   ├── logs_window.py
│   │   │   ├── system_hub_window.py
│   │   │   └── system_logs_service.py
│   │   ├── system_logs/
│   │   │   ├── system_logs_service.py
│   │   │   └── system_logs_window.py
│   │   ├── tools/
│   │   ├── workflow/
│   │   │   └── workflow_window.py
│   │   ├── __init__.py
│   │   └── ad_player.py
│   ├── rules_project/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ad_service.py
│   │   ├── ai_chatbot_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   ├── backup_tool.py
│   │   ├── barcode_service.py
│   │   ├── bi_service.py
│   │   ├── cache_service.py
│   │   ├── chart_service.py
│   │   ├── database_optimizer.py
│   │   ├── encryption_service.py
│   │   ├── export_service.py
│   │   ├── hotkey_manager.py
│   │   ├── i18n_service.py
│   │   ├── image_cache_service.py
│   │   ├── import_export_service.py
│   │   ├── lazy_load_service.py
│   │   ├── license_service.py
│   │   ├── logistics_service.py
│   │   ├── memory_service.py
│   │   ├── nl_query_service.py
│   │   ├── notification_service.py
│   │   ├── offline_queue.py
│   │   ├── payment_service.py
│   │   ├── performance_service.py
│   │   ├── permission_service.py
│   │   ├── print_service.py
│   │   ├── realtime_service.py
│   │   ├── sales_prediction_service.py
│   │   ├── scheduler_service.py
│   │   ├── sms_service.py
│   │   ├── sync_manager.py
│   │   ├── system_service.py
│   │   ├── system_tray.py
│   │   ├── template_service.py
│   │   ├── theme_service.py
│   │   ├── update_service.py
│   │   └── workflow_service.py
│   ├── shapes/
│   │   ├── __init__.py
│   │   ├── alien.py
│   │   ├── black_hole.py
│   │   ├── classic.py
│   │   ├── classic_20260614_184255_598.py
│   │   ├── comet.py
│   │   ├── corvette.py
│   │   ├── crystal_alien.py
│   │   ├── destroyer.py
│   │   ├── dreadnought.py
│   │   ├── energy_being.py
│   │   ├── fighter.py
│   │   ├── gas_giant.py
│   │   ├── gas_giant_20260614_184255_426.py
│   │   ├── ghost_alien.py
│   │   ├── grey_alien.py
│   │   ├── ice_giant.py
│   │   ├── ice_giant_20260614_184255_207.py
│   │   ├── interceptor.py
│   │   ├── jellyfish_alien.py
│   │   ├── lava_planet.py
│   │   ├── lava_planet_20260614_184255_101.py
│   │   ├── mars.py
│   │   ├── mars_20260614_184255_257.py
│   │   ├── mercury.py
│   │   ├── nebula.py
│   │   ├── neutron_star.py
│   │   ├── octopus_alien.py
│   │   ├── pluto.py
│   │   ├── pulsar.py
│   │   ├── red_giant.py
│   │   ├── reptilian.py
│   │   ├── robot_alien.py
│   │   ├── saturn.py
│   │   ├── scout.py
│   │   ├── starship.py
│   │   ├── transporter.py
│   │   ├── uranus.py
│   │   ├── venus.py
│   │   ├── white_dwarf.py
│   │   └── wormhole.py
│   ├── tests/
│   │   └── conftest.py
│   ├── tools/
│   │   ├── environments/
│   │   │   ├── __init__.py
│   │   │   └── file_sync.py
│   │   ├── __init__.py
│   │   └── skills_sync.py
│   ├── __init__.py
│   ├── _debug_run.py
│   ├── ad_launcher.py
│   ├── agent.py
│   ├── agent_loop.py
│   ├── app_state.py
│   ├── auth_service.py
│   ├── backup.py
│   ├── business_service.py
│   ├── ceo_agent.py
│   ├── chat_engine.py
│   ├── cloud_pull.py
│   ├── cloud_sync.py
│   ├── cloud_sync_v2.py
│   ├── code_executor.py
│   ├── code_intel.py
│   ├── conflict_resolver.py
│   ├── cosmic.py
│   ├── custom_fields.py
│   ├── dark_theme.py
│   ├── dark_tool_theme.py
│   ├── data.py
│   ├── data_sync.py
│   ├── database.py
│   ├── event_bus.py
│   ├── excel_export.py
│   ├── light_tool_theme.py
│   ├── llm_backend.py
│   ├── llm_client.py
│   ├── machine_code.py
│   ├── main.py
│   ├── mobile_api.py
│   ├── module_manager.py
│   ├── notification_cron.py
│   ├── notification_service.py
│   ├── notification_toast.py
│   ├── obscura_provider.py
│   ├── operation_log.py
│   ├── oplog.py
│   ├── patch_engine.py
│   ├── paths.py
│   ├── planet_daemon.py
│   ├── planet_painter.py
│   ├── procedural_texture.py
│   ├── reconciliation.py
│   ├── rollback_control.py
│   ├── scheduled_tasks.py
│   ├── simple_sync.py
│   ├── siri_command_handler.py
│   ├── smart_memory_adapter.py
│   ├── smart_report.py
│   ├── storage.py
│   ├── supabase_client.py
│   ├── sync_bridge.py
│   ├── sync_decorator.py
│   ├── sync_integration.py
│   ├── sync_manager.py
│   ├── task_scheduler.py
│   ├── texture_mapper.py
│   ├── theme.py
│   ├── tool_registry.py
│   ├── ui_components.py
│   ├── user_dao.py
│   ├── voice.py
│   ├── workflow_engine.py
│   └── workspace_indexer.py
├── data/
│   ├── sync/
├── iqra/
│   ├── _archived/
│   │   ├── data_20260619_122853/
│   │   ├── dedup_20260619_170800/
│   │   │   └── deps.py
│   │   └── license_模块归档_20260619/
│   │       ├── license_crypto.py
│   │       ├── license_db.py
│   │       └── license_service.py
│   ├── config/
│   │   ├── agents/
│   │   ├── __init__.py
│   │   ├── supabase_config.py
│   ├── core/
│   │   ├── _deprecated/
│   │   │   └── cloud_sync_v2.py
│   │   ├── harness/
│   │   │   ├── __init__.py
│   │   │   └── config_schema.py
│   │   ├── modules/
│   │   │   ├── supabase/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _core.py
│   │   │   │   ├── activation.py
│   │   │   │   ├── admin_log.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── business.py
│   │   │   │   ├── distribution.py
│   │   │   │   ├── member.py
│   │   │   │   ├── updater.py
│   │   │   │   └── wallet.py
│   │   │   └── __init__.py
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── cost_tracker.py
│   │   │   ├── schema.py
│   │   │   ├── token_observer.py
│   │   │   └── trace_manager.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── task_decompose.py
│   │   ├── shapes/
│   │   │   ├── __init__.py
│   │   │   ├── alien.py
│   │   │   ├── black_hole.py
│   │   │   ├── classic.py
│   │   │   ├── comet.py
│   │   │   ├── corvette.py
│   │   │   ├── crystal_alien.py
│   │   │   ├── destroyer.py
│   │   │   ├── dreadnought.py
│   │   │   ├── energy_being.py
│   │   │   ├── fighter.py
│   │   │   ├── gas_giant.py
│   │   │   ├── ghost_alien.py
│   │   │   ├── grey_alien.py
│   │   │   ├── ice_giant.py
│   │   │   ├── interceptor.py
│   │   │   ├── jellyfish_alien.py
│   │   │   ├── lava_planet.py
│   │   │   ├── mars.py
│   │   │   ├── mercury.py
│   │   │   ├── nebula.py
│   │   │   ├── neutron_star.py
│   │   │   ├── octopus_alien.py
│   │   │   ├── pluto.py
│   │   │   ├── pulsar.py
│   │   │   ├── red_giant.py
│   │   │   ├── reptilian.py
│   │   │   ├── robot_alien.py
│   │   │   ├── saturn.py
│   │   │   ├── scout.py
│   │   │   ├── starship.py
│   │   │   ├── transporter.py
│   │   │   ├── uranus.py
│   │   │   ├── venus.py
│   │   │   ├── white_dwarf.py
│   │   │   └── wormhole.py
│   │   ├── __init__.py
│   │   ├── _agent_events.py
│   │   ├── _agent_fallbacks.py
│   │   ├── _agent_loop_base.py
│   │   ├── _agent_loop_compat_mixin.py
│   │   ├── _agent_loop_exec_mixin.py
│   │   ├── _agent_prompts.py
│   │   ├── _backend_convenience.py
│   │   ├── _backend_factory.py
│   │   ├── _backend_models.py
│   │   ├── _backend_providers.py
│   │   ├── _backend_utils.py
│   │   ├── _base_backend.py
│   │   ├── _basic_tools.py
│   │   ├── _bm25.py
│   │   ├── _chunker.py
│   │   ├── _claude_tools.py
│   │   ├── _config_helpers.py
│   │   ├── _index_config.py
│   │   ├── _index_models.py
│   │   ├── _quick_funcs.py
│   │   ├── _test_llm_decompose.py
│   │   ├── _tokenizer.py
│   │   ├── _tool_registry.py
│   │   ├── ad_launcher.py
│   │   ├── agent.py
│   │   ├── agent_delegate.py
│   │   ├── agent_delegate_adapter.py
│   │   ├── agent_loop.py
│   │   ├── app_state.py
│   │   ├── auth_service.py
│   │   ├── backup.py
│   │   ├── book_search.py
│   │   ├── business_service.py
│   │   ├── ceo_agent.py
│   │   ├── chat_engine.py
│   │   ├── clarify_system.py
│   │   ├── cloud_pull.py
│   │   ├── cloud_sync.py
│   │   ├── code_executor.py
│   │   ├── code_intel.py
│   │   ├── collaboration_client.py
│   │   ├── config_validator.py
│   │   ├── conflict_resolver.py
│   │   ├── core_engine.py
│   │   ├── cosmic.py
│   │   ├── custom_fields.py
│   │   ├── dark_theme.py
│   │   ├── dark_tool_theme.py
│   │   ├── data.py
│   │   ├── data_sync.py
│   │   ├── database.py
│   │   ├── enhanced_core.py
│   │   ├── event_bus.py
│   │   ├── excel_export.py
│   │   ├── git_ops.py
│   │   ├── iqra_logging.py
│   │   ├── light_tool_theme.py
│   │   ├── llm_backend.py
│   │   ├── llm_client.py
│   │   ├── machine_code.py
│   │   ├── memory.py
│   │   ├── memory_store.py
│   │   ├── mobile_api.py
│   │   ├── model_status.py
│   │   ├── model_status_manager.py
│   │   ├── module_manager.py
│   │   ├── multi_model.py
│   │   ├── multi_model_chat_engine.py
│   │   ├── notification_cron.py
│   │   ├── notification_service.py
│   │   ├── notification_toast.py
│   │   ├── obscura_provider.py
│   │   ├── operation_log.py
│   │   ├── oplog.py
│   │   ├── patch_engine.py
│   │   ├── paths.py
│   │   ├── performance_monitor.py
│   │   ├── planet_painter.py
│   │   ├── proactive_engine.py
│   │   ├── proactive_monitors.py
│   │   ├── procedural_texture.py
│   │   ├── process_manager.py
│   │   ├── provider_registry.py
│   │   ├── rag_context.py
│   │   ├── reconciliation.py
│   │   ├── scheduled_tasks.py
│   │   ├── secure_storage.py
│   │   ├── semantic_search.py
│   │   ├── session_search.py
│   │   ├── simple_sync.py
│   │   ├── skill_loader.py
│   │   ├── skill_system.py
│   │   ├── smart_memory.py
│   │   ├── smart_memory_adapter.py
│   │   ├── smart_report.py
│   │   ├── storage.py
│   │   ├── supabase_client.py
│   │   ├── super_intelligence.py
│   │   ├── sync_bridge.py
│   │   ├── sync_decorator.py
│   │   ├── sync_integration.py
│   │   ├── sync_manager.py
│   │   ├── sync_optimized.py
│   │   ├── task_decomposer.py
│   │   ├── task_scheduler.py
│   │   ├── texture_mapper.py
│   │   ├── todo_system.py
│   │   ├── token_optimizer.py
│   │   ├── token_saver.py
│   │   ├── tool_registry.py
│   │   ├── triple_sync.py
│   │   ├── ui_components.py
│   │   ├── user_dao.py
│   │   ├── voice.py
│   │   ├── web_search.py
│   │   ├── workflow_engine.py
│   │   └── workspace_indexer.py
│   ├── data/
│   │   ├── ads/
│   │   │   └── videos/
│   │   ├── drafts/
│   │   ├── enhanced/
│   │   ├── iqra/
│   │   │   └── metrics/
│   │   ├── metrics/
│   │   ├── process_logs/
│   │   ├── sync/
│   ├── iqra/
│   │   └── data/
│   ├── knowledge_base/
│   ├── log/
│   ├── logs/
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── dao/
│   │   │   │   ├── user_dao.py
│   │   │   ├── model_config_panel/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _constants.py
│   │   │   │   ├── _dialog.py
│   │   │   │   ├── _panel_config.py
│   │   │   │   ├── _panel_custom.py
│   │   │   │   ├── _panel_local.py
│   │   │   │   ├── _panel_preset.py
│   │   │   │   ├── _panel_ui.py
│   │   │   │   └── _workers.py
│   │   │   ├── service/
│   │   │   │   └── cloud_api.py
│   │   │   ├── __init__.py
│   │   │   ├── activation_gate.py
│   │   │   ├── admin_login_dialog.py
│   │   │   ├── auth_service.py
│   │   │   ├── auth_service_membership.py
│   │   │   ├── auth_service_sync.py
│   │   │   ├── change_password_dialog.py
│   │   │   ├── connect_window.py
│   │   │   ├── login_window.py
│   │   │   ├── model_setup_window.py
│   │   │   ├── register_window.py
│   │   │   ├── select_mode_window.py
│   │   │   ├── upgrade_window.py
│   │   ├── dashboard/
│   │   │   ├── dashboard_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _account_tools.py
│   │   │   │   ├── _module_navigator.py
│   │   │   │   ├── _module_window.py
│   │   │   │   ├── _planets.py
│   │   │   │   ├── _renderer.py
│   │   │   │   └── _ui.py
│   │   │   └── dashboard_window.py
│   │   ├── intelligence/
│   │   │   ├── agent_bridge_tools/
│   │   │   │   ├── __test_temp/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _code_tools.py
│   │   │   │   ├── _file_tools.py
│   │   │   │   ├── _legacy_tools.py
│   │   │   │   ├── _system_tools.py
│   │   │   │   ├── _task_tools.py
│   │   │   │   └── _web_tools.py
│   │   │   ├── ai_chat_window/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _chat_stream.py
│   │   │   │   ├── _file_upload.py
│   │   │   │   ├── _misc.py
│   │   │   │   ├── _model_selector.py
│   │   │   │   ├── _session.py
│   │   │   │   ├── _ui.py
│   │   │   │   └── _voice.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   └── llm_backend.py
│   │   │   ├── data/
│   │   │   │   ├── learning/
│   │   │   │   └── reflections/
│   │   │   ├── enhanced/
│   │   │   │   ├── __init__.py
│   │   │   │   └── enhanced_tools.py
│   │   │   ├── __init__.py
│   │   │   ├── _ai_shared.py
│   │   │   ├── _ai_widgets.py
│   │   │   ├── _ai_widgets_anomaly.py
│   │   │   ├── _ai_widgets_business.py
│   │   │   ├── _ai_widgets_core.py
│   │   │   ├── _ai_widgets_recommendation.py
│   │   │   ├── _ai_widgets_visualization.py
│   │   │   ├── _ai_widgets_workflow.py
│   │   │   ├── _api_key_dialog.py
│   │   │   ├── _chat_dialog.py
│   │   │   ├── _compat.py
│   │   │   ├── _floating_planet_chat_mixin.py
│   │   │   ├── _floating_planet_input_mixin.py
│   │   │   ├── _floating_planet_modules_mixin.py
│   │   │   ├── _model_manager.py
│   │   │   ├── _model_manager_download.py
│   │   │   ├── _model_manager_ollama.py
│   │   │   ├── _navigation_hud.py
│   │   │   ├── _quick_tools_widget.py
│   │   │   ├── _shell_dialogs.py
│   │   │   ├── _stubs.py
│   │   │   ├── _text_crypto.py
│   │   │   ├── _text_editor_files_mixin.py
│   │   │   ├── _text_editor_format_mixin.py
│   │   │   ├── _text_editor_tree_mixin.py
│   │   │   ├── _text_editor_ui_mixin.py
│   │   │   ├── account_window.py
│   │   │   ├── agent_bridge.py
│   │   │   ├── agent_bridge_models.py
│   │   │   ├── agent_bridge_tools.py
│   │   │   ├── agent_bridge_workers.py
│   │   │   ├── ai_assistant_window.py
│   │   │   ├── ai_center_window.py
│   │   │   ├── ai_chat_styles.py
│   │   │   ├── ai_chat_window.py
│   │   │   ├── ai_dashboard_window.py
│   │   │   ├── ai_features_ai_dashboard.py
│   │   │   ├── ai_features_customer_ai.py
│   │   │   ├── ai_features_inventory_ai.py
│   │   │   ├── ai_features_pricing_ai.py
│   │   │   ├── ai_features_sales_ai.py
│   │   │   ├── analysis_tools.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── auto_task_executor.py
│   │   │   ├── batch_text.py
│   │   │   ├── business_ai_assistant.py
│   │   │   ├── business_tools.py
│   │   │   ├── chat_session_manager.py
│   │   │   ├── compress_tool.py
│   │   │   ├── crm_tools.py
│   │   │   ├── data_import_tools.py
│   │   │   ├── data_visualization.py
│   │   │   ├── db_helper.py
│   │   │   ├── download_dialog.py
│   │   │   ├── editor_window.py
│   │   │   ├── enhanced_chat.py
│   │   │   ├── event_trigger.py
│   │   │   ├── file_rename_tools.py
│   │   │   ├── finance_analysis_tools.py
│   │   │   ├── floating_planet.py
│   │   │   ├── floating_planet_anim_mixin.py
│   │   │   ├── floating_planet_draw_mixin.py
│   │   │   ├── floating_planet_menu_mixin.py
│   │   │   ├── hr_tools.py
│   │   │   ├── img_converter.py
│   │   │   ├── intelligence_integration.py
│   │   │   ├── intelligence_window.py
│   │   │   ├── inventory_tools.py
│   │   │   ├── iqra_floating_planet.py
│   │   │   ├── json_tools.py
│   │   │   ├── key_manager.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── marketing_tools.py
│   │   │   ├── model_config.py
│   │   │   ├── monitor_dashboard.py
│   │   │   ├── offline_analyzer.py
│   │   │   ├── password_tools.py
│   │   │   ├── performance_monitor.py
│   │   │   ├── predictor_window.py
│   │   │   ├── quick_actions.py
│   │   │   ├── quick_tools_panel.py
│   │   │   ├── rag_injector.py
│   │   │   ├── recommendation_engine.py
│   │   │   ├── report_generator.py
│   │   │   ├── sales_predictor.py
│   │   │   ├── scan_window.py
│   │   │   ├── screen_recorder.py
│   │   │   ├── self_monitor.py
│   │   │   ├── session_context.py
│   │   │   ├── smart_assistant.py
│   │   │   ├── smart_report_tools.py
│   │   │   ├── smart_workflow.py
│   │   │   ├── solar_system_data.py
│   │   │   ├── solar_system_window.py
│   │   │   ├── super_intelligence.py
│   │   │   ├── system_hub_window.py
│   │   │   ├── system_monitor.py
│   │   │   ├── text_editor.py
│   │   │   ├── timestamp_tools.py
│   │   │   ├── tool_registry.py
│   │   │   ├── tools_window.py
│   │   │   ├── usb_scanner.py
│   │   │   ├── vault_window.py
│   │   │   ├── voice_interface.py
│   │   │   ├── whisper_recognizer.py
│   │   │   ├── window_top_tools.py
│   │   │   └── workflow_engine.py
│   │   ├── iqra/
│   │   │   └── data/
│   │   └── __init__.py
│   ├── rules_project/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ad_service.py
│   │   ├── ai_chatbot_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   ├── backup_tool.py
│   │   ├── barcode_service.py
│   │   ├── bi_service.py
│   │   ├── cache_service.py
│   │   ├── chart_service.py
│   │   ├── database_optimizer.py
│   │   ├── encryption_service.py
│   │   ├── export_service.py
│   │   ├── hotkey_manager.py
│   │   ├── i18n_service.py
│   │   ├── image_cache_service.py
│   │   ├── import_export_service.py
│   │   ├── lazy_load_service.py
│   │   ├── license_service.py
│   │   ├── logistics_service.py
│   │   ├── memory_service.py
│   │   ├── nl_query_service.py
│   │   ├── notification_service.py
│   │   ├── offline_queue.py
│   │   ├── payment_service.py
│   │   ├── performance_service.py
│   │   ├── permission_service.py
│   │   ├── print_service.py
│   │   ├── realtime_service.py
│   │   ├── sales_prediction_service.py
│   │   ├── scheduler_service.py
│   │   ├── sms_service.py
│   │   ├── sync_manager.py
│   │   ├── system_service.py
│   │   ├── system_tray.py
│   │   ├── template_service.py
│   │   ├── theme_service.py
│   │   ├── update_service.py
│   │   └── workflow_service.py
│   ├── solar_explorer/
│   │   ├── __init__.py
│   │   ├── _dwarf_planets.py
│   │   ├── _moons.py
│   │   ├── _planets.py
│   │   ├── _sun.py
│   │   ├── body_data_entries.py
│   │   ├── body_detail_window.py
│   │   ├── body_encyclopedia.py
│   │   ├── star_catalog_window.py
│   │   └── voice_reader.py
│   ├── tools/
│   │   ├── environments/
│   │   │   ├── __init__.py
│   │   │   └── file_sync.py
│   │   ├── __init__.py
│   │   ├── check_imports.py
│   │   ├── module_health.py
│   │   └── skills_sync.py
│   ├── hermes_constants.py
│   ├── iqra_chat.py
│   ├── iqra_setup.py
│   ├── main.py
│   ├── planet_daemon.py
│   ├── rollback_control.py
│   ├── siri_command_handler.py
│   ├── utils.py
├── knowledge_base/
├── log/
├── management-system/
│   ├── _archived/
│   │   ├── data_20260619_122853/
│   │   ├── dedup_20260619_170800/
│   │   │   └── deps.py
│   │   └── license_模块归档_20260619/
│   │       ├── license_crypto.py
│   │       ├── license_db.py
│   │       └── license_service.py
│   ├── config/
│   │   ├── agents/
│   │   ├── __init__.py
│   │   ├── supabase_config.py
│   ├── core/
│   │   ├── _deprecated/
│   │   │   ├── cloud_sync_v2.py
│   │   │   ├── sync_optimized.py
│   │   │   └── triple_sync.py
│   │   ├── modules/
│   │   │   ├── intelligence/
│   │   │   ├── supabase/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _core.py
│   │   │   │   ├── activation.py
│   │   │   │   ├── admin_log.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── business.py
│   │   │   │   ├── distribution.py
│   │   │   │   ├── member.py
│   │   │   │   ├── updater.py
│   │   │   │   └── wallet.py
│   │   │   └── __init__.py
│   │   ├── services/
│   │   ├── shapes/
│   │   │   ├── __init__.py
│   │   │   ├── alien.py
│   │   │   ├── black_hole.py
│   │   │   ├── classic.py
│   │   │   ├── comet.py
│   │   │   ├── corvette.py
│   │   │   ├── crystal_alien.py
│   │   │   ├── destroyer.py
│   │   │   ├── dreadnought.py
│   │   │   ├── energy_being.py
│   │   │   ├── fighter.py
│   │   │   ├── gas_giant.py
│   │   │   ├── ghost_alien.py
│   │   │   ├── grey_alien.py
│   │   │   ├── ice_giant.py
│   │   │   ├── interceptor.py
│   │   │   ├── jellyfish_alien.py
│   │   │   ├── lava_planet.py
│   │   │   ├── mars.py
│   │   │   ├── mercury.py
│   │   │   ├── nebula.py
│   │   │   ├── neutron_star.py
│   │   │   ├── octopus_alien.py
│   │   │   ├── pluto.py
│   │   │   ├── pulsar.py
│   │   │   ├── red_giant.py
│   │   │   ├── reptilian.py
│   │   │   ├── robot_alien.py
│   │   │   ├── saturn.py
│   │   │   ├── scout.py
│   │   │   ├── starship.py
│   │   │   ├── transporter.py
│   │   │   ├── uranus.py
│   │   │   ├── venus.py
│   │   │   ├── white_dwarf.py
│   │   │   └── wormhole.py
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── app_state.py
│   │   ├── auth_service.py
│   │   ├── backup.py
│   │   ├── business_service.py
│   │   ├── ceo_agent.py
│   │   ├── cloud_pull.py
│   │   ├── cloud_sync.py
│   │   ├── conflict_resolver.py
│   │   ├── cosmic.py
│   │   ├── custom_fields.py
│   │   ├── dark_theme.py
│   │   ├── dark_tool_theme.py
│   │   ├── data.py
│   │   ├── data_sync.py
│   │   ├── database.py
│   │   ├── event_bus.py
│   │   ├── excel_export.py
│   │   ├── llm_client.py
│   │   ├── machine_code.py
│   │   ├── mobile_api.py
│   │   ├── module_manager.py
│   │   ├── notification_cron.py
│   │   ├── notification_service.py
│   │   ├── notification_toast.py
│   │   ├── operation_log.py
│   │   ├── oplog.py
│   │   ├── paths.py
│   │   ├── planet_painter.py
│   │   ├── procedural_texture.py
│   │   ├── reconciliation.py
│   │   ├── scheduled_tasks.py
│   │   ├── simple_sync.py
│   │   ├── smart_report.py
│   │   ├── storage.py
│   │   ├── supabase_client.py
│   │   ├── sync_bridge.py
│   │   ├── sync_decorator.py
│   │   ├── sync_integration.py
│   │   ├── sync_manager.py
│   │   ├── texture_mapper.py
│   │   ├── theme.py
│   │   ├── user_dao.py
│   │   ├── voice.py
│   │   └── workflow_engine.py
│   ├── data/
│   │   ├── ads/
│   │   │   └── videos/
│   │   ├── drafts/
│   │   ├── enhanced/
│   │   ├── metrics/
│   │   ├── sync/
│   ├── iqra/
│   │   └── data/
│   ├── knowledge_base/
│   ├── log/
│   ├── modules/
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin_activation.py
│   │   │   ├── admin_backup.py
│   │   │   ├── admin_data.py
│   │   │   ├── admin_data_mgmt.py
│   │   │   ├── admin_finance.py
│   │   │   ├── admin_log.py
│   │   │   ├── admin_orders.py
│   │   │   ├── admin_product.py
│   │   │   ├── admin_service.py
│   │   │   ├── admin_settings.py
│   │   │   ├── admin_staff.py
│   │   │   ├── admin_strategy.py
│   │   │   ├── admin_user.py
│   │   │   ├── admin_window.py
│   │   │   ├── cascade_delete.py
│   │   │   └── strategy_dao.py
│   │   ├── auth/
│   │   │   ├── dao/
│   │   │   ├── model_config_panel/
│   │   │   ├── service/
│   │   │   ├── __init__.py
│   │   │   ├── upgrade_window.py
│   │   ├── system/
│   │   │   ├── _archived/
│   │   │   ├── __init__.py
│   │   │   ├── cloud_model_panel.py
│   │   │   ├── cloud_module.py
│   │   │   ├── cloud_server_window.py
│   │   │   └── cloud_window.py
│   │   └── __init__.py
│   ├── rules_project/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_chatbot_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   ├── backup_tool.py
│   │   ├── barcode_service.py
│   │   ├── bi_service.py
│   │   ├── cache_service.py
│   │   ├── chart_service.py
│   │   ├── database_optimizer.py
│   │   ├── encryption_service.py
│   │   ├── export_service.py
│   │   ├── i18n_service.py
│   │   ├── image_cache_service.py
│   │   ├── import_export_service.py
│   │   ├── lazy_load_service.py
│   │   ├── license_service.py
│   │   ├── logistics_service.py
│   │   ├── memory_service.py
│   │   ├── nl_query_service.py
│   │   ├── notification_service.py
│   │   ├── offline_queue.py
│   │   ├── payment_service.py
│   │   ├── performance_service.py
│   │   ├── permission_service.py
│   │   ├── print_service.py
│   │   ├── realtime_service.py
│   │   ├── sales_prediction_service.py
│   │   ├── scheduler_service.py
│   │   ├── sms_service.py
│   │   ├── sync_manager.py
│   │   ├── system_service.py
│   │   ├── system_tray.py
│   │   ├── template_service.py
│   │   ├── theme_service.py
│   │   ├── update_service.py
│   │   └── workflow_service.py
│   ├── tools/
│   │   ├── environments/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── rollback_control.py
│   ├── siri_command_handler.py
├── modules/
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── admin_activation.py
│   │   ├── admin_backup.py
│   │   ├── admin_data.py
│   │   ├── admin_data_mgmt.py
│   │   ├── admin_finance.py
│   │   ├── admin_log.py
│   │   ├── admin_orders.py
│   │   ├── admin_product.py
│   │   ├── admin_service.py
│   │   ├── admin_settings.py
│   │   ├── admin_staff.py
│   │   ├── admin_strategy.py
│   │   ├── admin_user.py
│   │   ├── admin_window.py
│   │   ├── cascade_delete.py
│   │   └── strategy_dao.py
│   ├── astronomy/
│   │   ├── solar_system/
│   │   │   ├── planets/
│   │   │   │   ├── callisto/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── ceres/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── earth/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── enceladus/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── eris/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── europa/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── ganymede/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── haumea/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── io/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── jupiter/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── makemake/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── mars/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── mercury/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── moon/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── neptune/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── pluto/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── saturn/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── sun/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── titan/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── uranus/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── venus/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── _base.py
│   │   │   ├── __init__.py
│   │   │   ├── data.py
│   │   │   ├── renderer.py
│   │   │   └── window.py
│   │   ├── star_catalog/
│   │   │   ├── __init__.py
│   │   │   ├── catalog.py
│   │   │   ├── data_entries.py
│   │   │   ├── detail.py
│   │   │   ├── encyclopedia.py
│   │   │   └── voice.py
│   │   ├── __init__.py
│   │   └── hub.py
│   ├── auth/
│   │   ├── dao/
│   │   │   ├── __init__.py
│   │   │   ├── session_dao.py
│   │   │   └── user_dao.py
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── auth_service_membership.py
│   │   ├── auth_service_sync.py
│   │   ├── login_window.py
│   │   ├── model_setup_window.py
│   ├── intelligence/
│   │   ├── __init__.py
│   │   └── solar_system_data.py
│   ├── supabase/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── system/
│   │   ├── _archived/
│   │   │   ├── activation_window.py
│   │   │   ├── base_info_window.py
│   │   │   ├── cloud_window.py
│   │   │   ├── logs_window.py
│   │   │   ├── system_window.py
│   │   │   └── update_dialog.py
│   │   ├── __init__.py
│   │   ├── astronomy_hub_window.py
│   │   ├── audit_window.py
│   │   ├── base_info_window.py
│   │   ├── cloud_model_panel.py
│   │   ├── cloud_module.py
│   │   ├── cloud_server_window.py
│   │   ├── cloud_window.py
│   │   ├── logs_window.py
│   │   ├── system_hub_window.py
│   │   └── system_logs_service.py
│   └── __init__.py
├── one_person_company.egg-info/
├── planetarium/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── supabase_config.py
│   ├── core/
│   │   ├── _deprecated/
│   │   │   ├── cloud_sync_v2.py
│   │   │   ├── sync_optimized.py
│   │   │   └── triple_sync.py
│   │   ├── modules/
│   │   │   ├── intelligence/
│   │   │   │   ├── _chat_dialog/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── _dialog.py
│   │   │   │   ├── agent_bridge/
│   │   │   │   │   ├── agent_bridge_tools/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── _code_tools.py
│   │   │   │   │   │   ├── _file_tools.py
│   │   │   │   │   │   ├── _system_tools.py
│   │   │   │   │   │   ├── _task_tools.py
│   │   │   │   │   │   └── _web_tools.py
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _core.py
│   │   │   │   │   ├── _engine_mixin.py
│   │   │   │   │   ├── agent_bridge_models.py
│   │   │   │   │   └── agent_bridge_workers.py
│   │   │   │   ├── enhanced/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _enhanced_base.py
│   │   │   │   │   ├── _enhanced_files_mixin.py
│   │   │   │   │   ├── _enhanced_storage_mixin.py
│   │   │   │   │   ├── _enhanced_system_mixin.py
│   │   │   │   │   ├── _enhanced_web_mixin.py
│   │   │   │   │   └── enhanced_tools.py
│   │   │   │   ├── marketing_tools/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _core.py
│   │   │   │   │   └── _registration.py
│   │   │   │   ├── quick_tools_panel/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _api_config.py
│   │   │   │   │   └── _quick_tools.py
│   │   │   │   ├── solar_system_data/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _catalog.py
│   │   │   │   │   ├── _core.py
│   │   │   │   │   └── _data.py
│   │   │   │   ├── text_editor/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _core.py
│   │   │   │   │   ├── _crypto.py
│   │   │   │   │   └── _note_tab.py
│   │   │   │   ├── workflow_engine/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _engine.py
│   │   │   │   │   └── _models.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _ai_shared.py
│   │   │   │   ├── _chat_dialog.py
│   │   │   │   ├── _compat.py
│   │   │   │   ├── _model_manager_download.py
│   │   │   │   ├── _model_manager_ollama.py
│   │   │   │   ├── _stubs.py
│   │   │   │   ├── agent_bridge.py
│   │   │   │   ├── intelligence_integration.py
│   │   │   │   ├── marketing_tools.py
│   │   │   │   ├── quick_tools_panel.py
│   │   │   │   ├── session_context.py
│   │   │   │   ├── solar_system_data.py
│   │   │   │   ├── super_intelligence.py
│   │   │   │   ├── text_editor.py
│   │   │   │   ├── tool_registry.py
│   │   │   │   └── workflow_engine.py
│   │   │   ├── supabase/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _core.py
│   │   │   │   ├── activation.py
│   │   │   │   ├── admin_log.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── business.py
│   │   │   │   ├── distribution.py
│   │   │   │   ├── member.py
│   │   │   │   ├── updater.py
│   │   │   │   └── wallet.py
│   │   │   └── __init__.py
│   │   ├── shapes/
│   │   │   ├── __init__.py
│   │   │   ├── alien.py
│   │   │   ├── black_hole.py
│   │   │   ├── classic.py
│   │   │   ├── classic_20260614_184255_598.py
│   │   │   ├── comet.py
│   │   │   ├── corvette.py
│   │   │   ├── crystal_alien.py
│   │   │   ├── destroyer.py
│   │   │   ├── dreadnought.py
│   │   │   ├── energy_being.py
│   │   │   ├── fighter.py
│   │   │   ├── gas_giant.py
│   │   │   ├── gas_giant_20260614_184255_426.py
│   │   │   ├── ghost_alien.py
│   │   │   ├── grey_alien.py
│   │   │   ├── ice_giant.py
│   │   │   ├── ice_giant_20260614_184255_207.py
│   │   │   ├── interceptor.py
│   │   │   ├── jellyfish_alien.py
│   │   │   ├── lava_planet.py
│   │   │   ├── lava_planet_20260614_184255_101.py
│   │   │   ├── mars.py
│   │   │   ├── mars_20260614_184255_257.py
│   │   │   ├── mercury.py
│   │   │   ├── nebula.py
│   │   │   ├── neutron_star.py
│   │   │   ├── octopus_alien.py
│   │   │   ├── pluto.py
│   │   │   ├── pulsar.py
│   │   │   ├── red_giant.py
│   │   │   ├── reptilian.py
│   │   │   ├── robot_alien.py
│   │   │   ├── saturn.py
│   │   │   ├── scout.py
│   │   │   ├── starship.py
│   │   │   ├── transporter.py
│   │   │   ├── uranus.py
│   │   │   ├── venus.py
│   │   │   ├── white_dwarf.py
│   │   │   └── wormhole.py
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── app_state.py
│   │   ├── auth_service.py
│   │   ├── backup.py
│   │   ├── cloud_pull.py
│   │   ├── cloud_sync.py
│   │   ├── conflict_resolver.py
│   │   ├── cosmic.py
│   │   ├── dark_theme.py
│   │   ├── dark_tool_theme.py
│   │   ├── data.py
│   │   ├── data_sync.py
│   │   ├── database.py
│   │   ├── event_bus.py
│   │   ├── llm_client.py
│   │   ├── machine_code.py
│   │   ├── module_manager.py
│   │   ├── notification_cron.py
│   │   ├── notification_service.py
│   │   ├── notification_toast.py
│   │   ├── operation_log.py
│   │   ├── oplog.py
│   │   ├── paths.py
│   │   ├── planet_painter.py
│   │   ├── procedural_texture.py
│   │   ├── reconciliation.py
│   │   ├── scheduled_tasks.py
│   │   ├── simple_sync.py
│   │   ├── storage.py
│   │   ├── supabase_client.py
│   │   ├── sync_bridge.py
│   │   ├── sync_decorator.py
│   │   ├── sync_integration.py
│   │   ├── sync_manager.py
│   │   ├── texture_mapper.py
│   │   ├── user_dao.py
│   │   ├── voice.py
│   │   └── workflow_engine.py
│   ├── data/
│   ├── knowledge_base/
│   ├── log/
│   ├── rules_project/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_chatbot_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   ├── backup_tool.py
│   │   ├── barcode_service.py
│   │   ├── cache_service.py
│   │   ├── encryption_service.py
│   │   ├── i18n_service.py
│   │   ├── image_cache_service.py
│   │   ├── lazy_load_service.py
│   │   ├── license_service.py
│   │   ├── memory_service.py
│   │   ├── notification_service.py
│   │   ├── offline_queue.py
│   │   ├── performance_service.py
│   │   ├── scheduler_service.py
│   │   ├── sync_manager.py
│   │   ├── system_tray.py
│   │   ├── theme_service.py
│   │   └── update_service.py
│   ├── shapes/
│   │   ├── __init__.py
│   │   ├── alien.py
│   │   ├── black_hole.py
│   │   ├── classic.py
│   │   ├── comet.py
│   │   ├── corvette.py
│   │   ├── crystal_alien.py
│   │   ├── destroyer.py
│   │   ├── dreadnought.py
│   │   ├── energy_being.py
│   │   ├── fighter.py
│   │   ├── gas_giant.py
│   │   ├── ghost_alien.py
│   │   ├── grey_alien.py
│   │   ├── ice_giant.py
│   │   ├── interceptor.py
│   │   ├── jellyfish_alien.py
│   │   ├── lava_planet.py
│   │   ├── mars.py
│   │   ├── mercury.py
│   │   ├── nebula.py
│   │   ├── neutron_star.py
│   │   ├── octopus_alien.py
│   │   ├── pluto.py
│   │   ├── pulsar.py
│   │   ├── red_giant.py
│   │   ├── reptilian.py
│   │   ├── robot_alien.py
│   │   ├── saturn.py
│   │   ├── scout.py
│   │   ├── starship.py
│   │   ├── transporter.py
│   │   ├── uranus.py
│   │   ├── venus.py
│   │   ├── white_dwarf.py
│   │   └── wormhole.py
│   ├── tools/
│   │   ├── environments/
│   │   │   └── __init__.py
│   │   └── __init__.py
├── solar_explorer/
│   ├── __init__.py
│   ├── body_data_entries.py
│   ├── body_detail_window.py
│   ├── body_encyclopedia.py
│   ├── star_catalog_window.py
│   └── voice_reader.py
├── tests/
├── tools/
│   ├── clean_package.py
│   └── pack_build.py
├── gen_book.py
├── test_sync_30_tables.py
└── verify_both.py
```

---

## 模块列表

- [`_archive/core/data_20260619_111935_141.py`](./_archive/core/data_20260619_111935_141.py.md)
- [`_archive/core/planet_painter_20260614_151048_302.py`](./_archive/core/planet_painter_20260614_151048_302.py.md)
- [`_archive/core/shapes/classic_20260614_184255_598.py`](./_archive/core/shapes/classic_20260614_184255_598.py.md)
- [`_archive/core/shapes/gas_giant_20260614_184255_426.py`](./_archive/core/shapes/gas_giant_20260614_184255_426.py.md)
- [`_archive/core/shapes/ice_giant_20260614_184255_207.py`](./_archive/core/shapes/ice_giant_20260614_184255_207.py.md)
- [`_archive/core/shapes/lava_planet_20260614_184255_101.py`](./_archive/core/shapes/lava_planet_20260614_184255_101.py.md)
- [`_archive/core/shapes/mars_20260614_184255_257.py`](./_archive/core/shapes/mars_20260614_184255_257.py.md)
- [`_archive/iqra/core/data_20260619_111935_141.py`](./_archive/iqra/core/data_20260619_111935_141.py.md)
- [`_archive/iqra/core/planet_painter_20260614_151048_302.py`](./_archive/iqra/core/planet_painter_20260614_151048_302.py.md)
- [`_archive/iqra/core/shapes/classic_20260614_184255_598.py`](./_archive/iqra/core/shapes/classic_20260614_184255_598.py.md)
- [`_archive/iqra/core/shapes/gas_giant_20260614_184255_426.py`](./_archive/iqra/core/shapes/gas_giant_20260614_184255_426.py.md)
- [`_archive/iqra/core/shapes/ice_giant_20260614_184255_207.py`](./_archive/iqra/core/shapes/ice_giant_20260614_184255_207.py.md)
- [`_archive/iqra/core/shapes/lava_planet_20260614_184255_101.py`](./_archive/iqra/core/shapes/lava_planet_20260614_184255_101.py.md)
- [`_archive/iqra/core/shapes/mars_20260614_184255_257.py`](./_archive/iqra/core/shapes/mars_20260614_184255_257.py.md)
- [`_archive/management-system/core/data_20260619_111935_141.py`](./_archive/management-system/core/data_20260619_111935_141.py.md)
- [`_archive/management-system/core/planet_painter_20260614_151048_302.py`](./_archive/management-system/core/planet_painter_20260614_151048_302.py.md)
- [`_archive/management-system/core/shapes/classic_20260614_184255_598.py`](./_archive/management-system/core/shapes/classic_20260614_184255_598.py.md)
- [`_archive/management-system/core/shapes/gas_giant_20260614_184255_426.py`](./_archive/management-system/core/shapes/gas_giant_20260614_184255_426.py.md)
- [`_archive/management-system/core/shapes/ice_giant_20260614_184255_207.py`](./_archive/management-system/core/shapes/ice_giant_20260614_184255_207.py.md)
- [`_archive/management-system/core/shapes/lava_planet_20260614_184255_101.py`](./_archive/management-system/core/shapes/lava_planet_20260614_184255_101.py.md)
- [`_archive/management-system/core/shapes/mars_20260614_184255_257.py`](./_archive/management-system/core/shapes/mars_20260614_184255_257.py.md)
- [`_archive/planetarium/core/shapes/classic_20260614_184255_598.py`](./_archive/planetarium/core/shapes/classic_20260614_184255_598.py.md)
- [`_archive/planetarium/core/shapes/gas_giant_20260614_184255_426.py`](./_archive/planetarium/core/shapes/gas_giant_20260614_184255_426.py.md)
- [`_archive/planetarium/core/shapes/ice_giant_20260614_184255_207.py`](./_archive/planetarium/core/shapes/ice_giant_20260614_184255_207.py.md)
- [`_archive/planetarium/core/shapes/lava_planet_20260614_184255_101.py`](./_archive/planetarium/core/shapes/lava_planet_20260614_184255_101.py.md)
- [`_archive/planetarium/core/shapes/mars_20260614_184255_257.py`](./_archive/planetarium/core/shapes/mars_20260614_184255_257.py.md)
- [`config/__init__.py`](./config/__init__.py.md)
- [`config/supabase_config.py`](./config/supabase_config.py.md)
- [`core/__init__.py`](./core/__init__.py.md)
- [`core/_debug_run.py`](./core/_debug_run.py.md)
- [`core/_deprecated/cloud_sync_v2.py`](./core/_deprecated/cloud_sync_v2.py.md)
- [`core/_deprecated/sync_optimized.py`](./core/_deprecated/sync_optimized.py.md)
- [`core/_deprecated/triple_sync.py`](./core/_deprecated/triple_sync.py.md)
- [`core/ad_launcher.py`](./core/ad_launcher.py.md)
- [`core/agent.py`](./core/agent.py.md)
- [`core/agent_loop.py`](./core/agent_loop.py.md)
- [`core/app_state.py`](./core/app_state.py.md)
- [`core/auth_service.py`](./core/auth_service.py.md)
- [`core/backup.py`](./core/backup.py.md)
- [`core/business_service.py`](./core/business_service.py.md)
- [`core/ceo_agent.py`](./core/ceo_agent.py.md)
- [`core/chat_engine.py`](./core/chat_engine.py.md)
- [`core/cloud_pull.py`](./core/cloud_pull.py.md)
- [`core/cloud_sync.py`](./core/cloud_sync.py.md)
- [`core/cloud_sync_v2.py`](./core/cloud_sync_v2.py.md)
- [`core/code_executor.py`](./core/code_executor.py.md)
- [`core/code_intel.py`](./core/code_intel.py.md)
- [`core/config/supabase_config.py`](./core/config/supabase_config.py.md)
- [`core/conflict_resolver.py`](./core/conflict_resolver.py.md)
- [`core/cosmic.py`](./core/cosmic.py.md)
- [`core/custom_fields.py`](./core/custom_fields.py.md)
- [`core/dark_theme.py`](./core/dark_theme.py.md)
- [`core/dark_tool_theme.py`](./core/dark_tool_theme.py.md)
- [`core/data.py`](./core/data.py.md)
- [`core/data_sync.py`](./core/data_sync.py.md)
- [`core/database.py`](./core/database.py.md)
- [`core/event_bus.py`](./core/event_bus.py.md)
- [`core/excel_export.py`](./core/excel_export.py.md)
- [`core/light_tool_theme.py`](./core/light_tool_theme.py.md)
- [`core/llm_backend.py`](./core/llm_backend.py.md)
- [`core/llm_client.py`](./core/llm_client.py.md)
- [`core/machine_code.py`](./core/machine_code.py.md)
- [`core/main.py`](./core/main.py.md)
- [`core/mobile_api.py`](./core/mobile_api.py.md)
- [`core/module_manager.py`](./core/module_manager.py.md)
- [`core/modules/__init__.py`](./core/modules/__init__.py.md)
- [`core/modules/account/__init__.py`](./core/modules/account/__init__.py.md)
- [`core/modules/account/account_activation.py`](./core/modules/account/account_activation.py.md)
- [`core/modules/account/account_update.py`](./core/modules/account/account_update.py.md)
- [`core/modules/account/activation_service.py`](./core/modules/account/activation_service.py.md)
- [`core/modules/account/activation_stats.py`](./core/modules/account/activation_stats.py.md)
- [`core/modules/account/activation_stats_service.py`](./core/modules/account/activation_stats_service.py.md)
- [`core/modules/account/license_local.py`](./core/modules/account/license_local.py.md)
- [`core/modules/ad_player.py`](./core/modules/ad_player.py.md)
- [`core/modules/admin/__init__.py`](./core/modules/admin/__init__.py.md)
- [`core/modules/admin/admin_activation.py`](./core/modules/admin/admin_activation.py.md)
- [`core/modules/admin/admin_backup.py`](./core/modules/admin/admin_backup.py.md)
- [`core/modules/admin/admin_data.py`](./core/modules/admin/admin_data.py.md)
- [`core/modules/admin/admin_data_mgmt.py`](./core/modules/admin/admin_data_mgmt.py.md)
- [`core/modules/admin/admin_finance.py`](./core/modules/admin/admin_finance.py.md)
- [`core/modules/admin/admin_log.py`](./core/modules/admin/admin_log.py.md)
- [`core/modules/admin/admin_orders.py`](./core/modules/admin/admin_orders.py.md)
- [`core/modules/admin/admin_product.py`](./core/modules/admin/admin_product.py.md)
- [`core/modules/admin/admin_service.py`](./core/modules/admin/admin_service.py.md)
- [`core/modules/admin/admin_settings.py`](./core/modules/admin/admin_settings.py.md)
- [`core/modules/admin/admin_staff.py`](./core/modules/admin/admin_staff.py.md)
- [`core/modules/admin/admin_strategy.py`](./core/modules/admin/admin_strategy.py.md)
- [`core/modules/admin/admin_user.py`](./core/modules/admin/admin_user.py.md)
- [`core/modules/admin/admin_window.py`](./core/modules/admin/admin_window.py.md)
- [`core/modules/admin/cascade_delete.py`](./core/modules/admin/cascade_delete.py.md)
- [`core/modules/admin/strategy_dao.py`](./core/modules/admin/strategy_dao.py.md)
- [`core/modules/astronomy/__init__.py`](./core/modules/astronomy/__init__.py.md)
- [`core/modules/astronomy/hub.py`](./core/modules/astronomy/hub.py.md)
- [`core/modules/astronomy/solar_system/__init__.py`](./core/modules/astronomy/solar_system/__init__.py.md)
- [`core/modules/astronomy/solar_system/ad_player.py`](./core/modules/astronomy/solar_system/ad_player.py.md)
- [`core/modules/astronomy/solar_system/data.py`](./core/modules/astronomy/solar_system/data.py.md)
- [`core/modules/astronomy/solar_system/planets/__init__.py`](./core/modules/astronomy/solar_system/planets/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/_base.py`](./core/modules/astronomy/solar_system/planets/_base.py.md)
- [`core/modules/astronomy/solar_system/planets/callisto/__init__.py`](./core/modules/astronomy/solar_system/planets/callisto/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/ceres/__init__.py`](./core/modules/astronomy/solar_system/planets/ceres/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/earth/__init__.py`](./core/modules/astronomy/solar_system/planets/earth/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/enceladus/__init__.py`](./core/modules/astronomy/solar_system/planets/enceladus/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/eris/__init__.py`](./core/modules/astronomy/solar_system/planets/eris/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/europa/__init__.py`](./core/modules/astronomy/solar_system/planets/europa/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/ganymede/__init__.py`](./core/modules/astronomy/solar_system/planets/ganymede/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/haumea/__init__.py`](./core/modules/astronomy/solar_system/planets/haumea/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/io/__init__.py`](./core/modules/astronomy/solar_system/planets/io/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/jupiter/__init__.py`](./core/modules/astronomy/solar_system/planets/jupiter/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/makemake/__init__.py`](./core/modules/astronomy/solar_system/planets/makemake/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/mars/__init__.py`](./core/modules/astronomy/solar_system/planets/mars/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/mercury/__init__.py`](./core/modules/astronomy/solar_system/planets/mercury/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/moon/__init__.py`](./core/modules/astronomy/solar_system/planets/moon/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/neptune/__init__.py`](./core/modules/astronomy/solar_system/planets/neptune/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/pluto/__init__.py`](./core/modules/astronomy/solar_system/planets/pluto/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/saturn/__init__.py`](./core/modules/astronomy/solar_system/planets/saturn/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/sun/__init__.py`](./core/modules/astronomy/solar_system/planets/sun/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/titan/__init__.py`](./core/modules/astronomy/solar_system/planets/titan/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/uranus/__init__.py`](./core/modules/astronomy/solar_system/planets/uranus/__init__.py.md)
- [`core/modules/astronomy/solar_system/planets/venus/__init__.py`](./core/modules/astronomy/solar_system/planets/venus/__init__.py.md)
- [`core/modules/astronomy/solar_system/renderer.py`](./core/modules/astronomy/solar_system/renderer.py.md)
- [`core/modules/astronomy/solar_system/window/__init__.py`](./core/modules/astronomy/solar_system/window/__init__.py.md)
- [`core/modules/astronomy/solar_system/window/_colors.py`](./core/modules/astronomy/solar_system/window/_colors.py.md)
- [`core/modules/astronomy/solar_system/window/_hud.py`](./core/modules/astronomy/solar_system/window/_hud.py.md)
- [`core/modules/astronomy/solar_system/window/_window.py`](./core/modules/astronomy/solar_system/window/_window.py.md)
- [`core/modules/astronomy/solar_system/window.py`](./core/modules/astronomy/solar_system/window.py.md)
- [`core/modules/astronomy/star_catalog/__init__.py`](./core/modules/astronomy/star_catalog/__init__.py.md)
- [`core/modules/astronomy/star_catalog/catalog.py`](./core/modules/astronomy/star_catalog/catalog.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/__init__.py`](./core/modules/astronomy/star_catalog/data_entries/__init__.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_collections.py`](./core/modules/astronomy/star_catalog/data_entries/_collections.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_dwarf_planets.py`](./core/modules/astronomy/star_catalog/data_entries/_dwarf_planets.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_earth.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_earth.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_jupiter.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_jupiter.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_neptune.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_neptune.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_pluto.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_pluto.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_saturn.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_saturn.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_moons_uranus.py`](./core/modules/astronomy/star_catalog/data_entries/_moons_uranus.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_planets.py`](./core/modules/astronomy/star_catalog/data_entries/_planets.py.md)
- [`core/modules/astronomy/star_catalog/data_entries/_sun.py`](./core/modules/astronomy/star_catalog/data_entries/_sun.py.md)
- [`core/modules/astronomy/star_catalog/data_entries.py`](./core/modules/astronomy/star_catalog/data_entries.py.md)
- [`core/modules/astronomy/star_catalog/detail.py`](./core/modules/astronomy/star_catalog/detail.py.md)
- [`core/modules/astronomy/star_catalog/encyclopedia.py`](./core/modules/astronomy/star_catalog/encyclopedia.py.md)
- [`core/modules/astronomy/star_catalog/voice.py`](./core/modules/astronomy/star_catalog/voice.py.md)
- [`core/modules/auth/__init__.py`](./core/modules/auth/__init__.py.md)
- [`core/modules/auth/activation_gate.py`](./core/modules/auth/activation_gate.py.md)
- [`core/modules/auth/admin_login_dialog.py`](./core/modules/auth/admin_login_dialog.py.md)
- [`core/modules/auth/auth_service.py`](./core/modules/auth/auth_service.py.md)
- [`core/modules/auth/auth_service_membership.py`](./core/modules/auth/auth_service_membership.py.md)
- [`core/modules/auth/auth_service_sync.py`](./core/modules/auth/auth_service_sync.py.md)
- [`core/modules/auth/change_password_dialog.py`](./core/modules/auth/change_password_dialog.py.md)
- [`core/modules/auth/connect_window.py`](./core/modules/auth/connect_window.py.md)
- [`core/modules/auth/dao/session_dao.py`](./core/modules/auth/dao/session_dao.py.md)
- [`core/modules/auth/dao/user_dao.py`](./core/modules/auth/dao/user_dao.py.md)
- [`core/modules/auth/login_window.py`](./core/modules/auth/login_window.py.md)
- [`core/modules/auth/model_config_panel/__init__.py`](./core/modules/auth/model_config_panel/__init__.py.md)
- [`core/modules/auth/model_config_panel/_constants.py`](./core/modules/auth/model_config_panel/_constants.py.md)
- [`core/modules/auth/model_config_panel/_dialog.py`](./core/modules/auth/model_config_panel/_dialog.py.md)
- [`core/modules/auth/model_config_panel/_panel_config.py`](./core/modules/auth/model_config_panel/_panel_config.py.md)
- [`core/modules/auth/model_config_panel/_panel_custom.py`](./core/modules/auth/model_config_panel/_panel_custom.py.md)
- [`core/modules/auth/model_config_panel/_panel_local.py`](./core/modules/auth/model_config_panel/_panel_local.py.md)
- [`core/modules/auth/model_config_panel/_panel_preset.py`](./core/modules/auth/model_config_panel/_panel_preset.py.md)
- [`core/modules/auth/model_config_panel/_panel_ui.py`](./core/modules/auth/model_config_panel/_panel_ui.py.md)
- [`core/modules/auth/model_config_panel/_workers.py`](./core/modules/auth/model_config_panel/_workers.py.md)
- [`core/modules/auth/model_setup_window.py`](./core/modules/auth/model_setup_window.py.md)
- [`core/modules/auth/register_window.py`](./core/modules/auth/register_window.py.md)
- [`core/modules/auth/select_mode_window.py`](./core/modules/auth/select_mode_window.py.md)
- [`core/modules/auth/service/cloud_api.py`](./core/modules/auth/service/cloud_api.py.md)
- [`core/modules/auth/service/session_service.py`](./core/modules/auth/service/session_service.py.md)
- [`core/modules/auth/service/sync_auth_service.py`](./core/modules/auth/service/sync_auth_service.py.md)
- [`core/modules/auth/upgrade_window.py`](./core/modules/auth/upgrade_window.py.md)
- [`core/modules/business/__init__.py`](./core/modules/business/__init__.py.md)
- [`core/modules/business/business_window.py`](./core/modules/business/business_window.py.md)
- [`core/modules/business/customer_service.py`](./core/modules/business/customer_service.py.md)
- [`core/modules/business/customer_window.py`](./core/modules/business/customer_window.py.md)
- [`core/modules/business/finance_service.py`](./core/modules/business/finance_service.py.md)
- [`core/modules/business/finance_window.py`](./core/modules/business/finance_window.py.md)
- [`core/modules/business/order_service.py`](./core/modules/business/order_service.py.md)
- [`core/modules/business/order_window.py`](./core/modules/business/order_window.py.md)
- [`core/modules/business/product_service.py`](./core/modules/business/product_service.py.md)
- [`core/modules/business/product_window.py`](./core/modules/business/product_window.py.md)
- [`core/modules/common/advanced_filter_window.py`](./core/modules/common/advanced_filter_window.py.md)
- [`core/modules/common/custom_field_window.py`](./core/modules/common/custom_field_window.py.md)
- [`core/modules/dashboard/dashboard_window/__init__.py`](./core/modules/dashboard/dashboard_window/__init__.py.md)
- [`core/modules/dashboard/dashboard_window/_account_tools.py`](./core/modules/dashboard/dashboard_window/_account_tools.py.md)
- [`core/modules/dashboard/dashboard_window/_module_navigator.py`](./core/modules/dashboard/dashboard_window/_module_navigator.py.md)
- [`core/modules/dashboard/dashboard_window/_module_window.py`](./core/modules/dashboard/dashboard_window/_module_window.py.md)
- [`core/modules/dashboard/dashboard_window/_planets.py`](./core/modules/dashboard/dashboard_window/_planets.py.md)
- [`core/modules/dashboard/dashboard_window/_renderer.py`](./core/modules/dashboard/dashboard_window/_renderer.py.md)
- [`core/modules/dashboard/dashboard_window/_ui.py`](./core/modules/dashboard/dashboard_window/_ui.py.md)
- [`core/modules/dashboard/dashboard_window.py`](./core/modules/dashboard/dashboard_window.py.md)
- [`core/modules/data_center/__init__.py`](./core/modules/data_center/__init__.py.md)
- [`core/modules/data_center/bi_window.py`](./core/modules/data_center/bi_window.py.md)
- [`core/modules/data_center/chart_window.py`](./core/modules/data_center/chart_window.py.md)
- [`core/modules/data_center/data_window.py`](./core/modules/data_center/data_window.py.md)
- [`core/modules/data_center/report_service.py`](./core/modules/data_center/report_service.py.md)
- [`core/modules/data_center/report_service_v2.py`](./core/modules/data_center/report_service_v2.py.md)
- [`core/modules/data_center/report_window.py`](./core/modules/data_center/report_window.py.md)
- [`core/modules/data_center/smart_report_window.py`](./core/modules/data_center/smart_report_window.py.md)
- [`core/modules/i18n/i18n_window.py`](./core/modules/i18n/i18n_window.py.md)
- [`core/modules/industry/industry_adapter.py`](./core/modules/industry/industry_adapter.py.md)
- [`core/modules/industry/industry_config.py`](./core/modules/industry/industry_config.py.md)
- [`core/modules/industry/industry_report.py`](./core/modules/industry/industry_report.py.md)
- [`core/modules/industry/industry_window.py`](./core/modules/industry/industry_window.py.md)
- [`core/modules/intelligence/__init__.py`](./core/modules/intelligence/__init__.py.md)
- [`core/modules/intelligence/_ai_shared.py`](./core/modules/intelligence/_ai_shared.py.md)
- [`core/modules/intelligence/_ai_widgets.py`](./core/modules/intelligence/_ai_widgets.py.md)
- [`core/modules/intelligence/_ai_widgets_anomaly.py`](./core/modules/intelligence/_ai_widgets_anomaly.py.md)
- [`core/modules/intelligence/_ai_widgets_business.py`](./core/modules/intelligence/_ai_widgets_business.py.md)
- [`core/modules/intelligence/_ai_widgets_core.py`](./core/modules/intelligence/_ai_widgets_core.py.md)
- [`core/modules/intelligence/_ai_widgets_recommendation.py`](./core/modules/intelligence/_ai_widgets_recommendation.py.md)
- [`core/modules/intelligence/_ai_widgets_visualization.py`](./core/modules/intelligence/_ai_widgets_visualization.py.md)
- [`core/modules/intelligence/_ai_widgets_workflow.py`](./core/modules/intelligence/_ai_widgets_workflow.py.md)
- [`core/modules/intelligence/_chat_dialog/__init__.py`](./core/modules/intelligence/_chat_dialog/__init__.py.md)
- [`core/modules/intelligence/_chat_dialog/_dialog.py`](./core/modules/intelligence/_chat_dialog/_dialog.py.md)
- [`core/modules/intelligence/_compat.py`](./core/modules/intelligence/_compat.py.md)
- [`core/modules/intelligence/_model_manager.py`](./core/modules/intelligence/_model_manager.py.md)
- [`core/modules/intelligence/_model_manager_download.py`](./core/modules/intelligence/_model_manager_download.py.md)
- [`core/modules/intelligence/_model_manager_ollama.py`](./core/modules/intelligence/_model_manager_ollama.py.md)
- [`core/modules/intelligence/_navigation_hud.py`](./core/modules/intelligence/_navigation_hud.py.md)
- [`core/modules/intelligence/_shell_dialogs.py`](./core/modules/intelligence/_shell_dialogs.py.md)
- [`core/modules/intelligence/_stubs.py`](./core/modules/intelligence/_stubs.py.md)
- [`core/modules/intelligence/account_window.py`](./core/modules/intelligence/account_window.py.md)
- [`core/modules/intelligence/agent_bridge.py`](./core/modules/intelligence/agent_bridge.py.md)
- [`core/modules/intelligence/agent_bridge_models.py`](./core/modules/intelligence/agent_bridge_models.py.md)
- [`core/modules/intelligence/agent_bridge_tools/__init__.py`](./core/modules/intelligence/agent_bridge_tools/__init__.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_code_tools.py`](./core/modules/intelligence/agent_bridge_tools/_code_tools.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_file_tools.py`](./core/modules/intelligence/agent_bridge_tools/_file_tools.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_legacy_tools.py`](./core/modules/intelligence/agent_bridge_tools/_legacy_tools.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_system_tools.py`](./core/modules/intelligence/agent_bridge_tools/_system_tools.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_task_tools.py`](./core/modules/intelligence/agent_bridge_tools/_task_tools.py.md)
- [`core/modules/intelligence/agent_bridge_tools/_web_tools.py`](./core/modules/intelligence/agent_bridge_tools/_web_tools.py.md)
- [`core/modules/intelligence/agent_bridge_workers.py`](./core/modules/intelligence/agent_bridge_workers.py.md)
- [`core/modules/intelligence/ai_assistant_window.py`](./core/modules/intelligence/ai_assistant_window.py.md)
- [`core/modules/intelligence/ai_center_window.py`](./core/modules/intelligence/ai_center_window.py.md)
- [`core/modules/intelligence/ai_chat_styles.py`](./core/modules/intelligence/ai_chat_styles.py.md)
- [`core/modules/intelligence/ai_chat_window/__init__.py`](./core/modules/intelligence/ai_chat_window/__init__.py.md)
- [`core/modules/intelligence/ai_chat_window/_chat_stream.py`](./core/modules/intelligence/ai_chat_window/_chat_stream.py.md)
- [`core/modules/intelligence/ai_chat_window/_file_upload.py`](./core/modules/intelligence/ai_chat_window/_file_upload.py.md)
- [`core/modules/intelligence/ai_chat_window/_misc.py`](./core/modules/intelligence/ai_chat_window/_misc.py.md)
- [`core/modules/intelligence/ai_chat_window/_model_selector.py`](./core/modules/intelligence/ai_chat_window/_model_selector.py.md)
- [`core/modules/intelligence/ai_chat_window/_session.py`](./core/modules/intelligence/ai_chat_window/_session.py.md)
- [`core/modules/intelligence/ai_chat_window/_ui.py`](./core/modules/intelligence/ai_chat_window/_ui.py.md)
- [`core/modules/intelligence/ai_chat_window/_voice.py`](./core/modules/intelligence/ai_chat_window/_voice.py.md)
- [`core/modules/intelligence/ai_chat_window.py`](./core/modules/intelligence/ai_chat_window.py.md)
- [`core/modules/intelligence/ai_dashboard_window.py`](./core/modules/intelligence/ai_dashboard_window.py.md)
- [`core/modules/intelligence/ai_features_ai_dashboard.py`](./core/modules/intelligence/ai_features_ai_dashboard.py.md)
- [`core/modules/intelligence/ai_features_customer_ai.py`](./core/modules/intelligence/ai_features_customer_ai.py.md)
- [`core/modules/intelligence/ai_features_inventory_ai.py`](./core/modules/intelligence/ai_features_inventory_ai.py.md)
- [`core/modules/intelligence/ai_features_pricing_ai.py`](./core/modules/intelligence/ai_features_pricing_ai.py.md)
- [`core/modules/intelligence/ai_features_sales_ai.py`](./core/modules/intelligence/ai_features_sales_ai.py.md)
- [`core/modules/intelligence/analysis_tools.py`](./core/modules/intelligence/analysis_tools.py.md)
- [`core/modules/intelligence/anomaly_detector.py`](./core/modules/intelligence/anomaly_detector.py.md)
- [`core/modules/intelligence/auto_task_executor.py`](./core/modules/intelligence/auto_task_executor.py.md)
- [`core/modules/intelligence/backup_window.py`](./core/modules/intelligence/backup_window.py.md)
- [`core/modules/intelligence/batch_text.py`](./core/modules/intelligence/batch_text.py.md)
- [`core/modules/intelligence/business_ai_assistant.py`](./core/modules/intelligence/business_ai_assistant.py.md)
- [`core/modules/intelligence/business_tools.py`](./core/modules/intelligence/business_tools.py.md)
- [`core/modules/intelligence/chat_session_manager.py`](./core/modules/intelligence/chat_session_manager.py.md)
- [`core/modules/intelligence/compress_tool.py`](./core/modules/intelligence/compress_tool.py.md)
- [`core/modules/intelligence/core/__init__.py`](./core/modules/intelligence/core/__init__.py.md)
- [`core/modules/intelligence/core/llm_backend.py`](./core/modules/intelligence/core/llm_backend.py.md)
- [`core/modules/intelligence/crm_tools.py`](./core/modules/intelligence/crm_tools.py.md)
- [`core/modules/intelligence/data_import_tools.py`](./core/modules/intelligence/data_import_tools.py.md)
- [`core/modules/intelligence/data_visualization.py`](./core/modules/intelligence/data_visualization.py.md)
- [`core/modules/intelligence/db_helper.py`](./core/modules/intelligence/db_helper.py.md)
- [`core/modules/intelligence/download_dialog.py`](./core/modules/intelligence/download_dialog.py.md)
- [`core/modules/intelligence/editor_window.py`](./core/modules/intelligence/editor_window.py.md)
- [`core/modules/intelligence/enhanced/__init__.py`](./core/modules/intelligence/enhanced/__init__.py.md)
- [`core/modules/intelligence/enhanced/_enhanced_base.py`](./core/modules/intelligence/enhanced/_enhanced_base.py.md)
- [`core/modules/intelligence/enhanced/_enhanced_files_mixin.py`](./core/modules/intelligence/enhanced/_enhanced_files_mixin.py.md)
- [`core/modules/intelligence/enhanced/_enhanced_storage_mixin.py`](./core/modules/intelligence/enhanced/_enhanced_storage_mixin.py.md)
- [`core/modules/intelligence/enhanced/_enhanced_system_mixin.py`](./core/modules/intelligence/enhanced/_enhanced_system_mixin.py.md)
- [`core/modules/intelligence/enhanced/_enhanced_web_mixin.py`](./core/modules/intelligence/enhanced/_enhanced_web_mixin.py.md)
- [`core/modules/intelligence/enhanced/enhanced_tools.py`](./core/modules/intelligence/enhanced/enhanced_tools.py.md)
- [`core/modules/intelligence/enhanced_chat.py`](./core/modules/intelligence/enhanced_chat.py.md)
- [`core/modules/intelligence/event_trigger.py`](./core/modules/intelligence/event_trigger.py.md)
- [`core/modules/intelligence/file_rename_tools.py`](./core/modules/intelligence/file_rename_tools.py.md)
- [`core/modules/intelligence/finance_analysis_tools.py`](./core/modules/intelligence/finance_analysis_tools.py.md)
- [`core/modules/intelligence/floating_planet.py`](./core/modules/intelligence/floating_planet.py.md)
- [`core/modules/intelligence/floating_planet_anim_mixin.py`](./core/modules/intelligence/floating_planet_anim_mixin.py.md)
- [`core/modules/intelligence/floating_planet_draw_mixin.py`](./core/modules/intelligence/floating_planet_draw_mixin.py.md)
- [`core/modules/intelligence/floating_planet_menu_mixin.py`](./core/modules/intelligence/floating_planet_menu_mixin.py.md)
- [`core/modules/intelligence/hr_tools.py`](./core/modules/intelligence/hr_tools.py.md)
- [`core/modules/intelligence/img_converter.py`](./core/modules/intelligence/img_converter.py.md)
- [`core/modules/intelligence/intelligence_integration.py`](./core/modules/intelligence/intelligence_integration.py.md)
- [`core/modules/intelligence/intelligence_window.py`](./core/modules/intelligence/intelligence_window.py.md)
- [`core/modules/intelligence/inventory_tools.py`](./core/modules/intelligence/inventory_tools.py.md)
- [`core/modules/intelligence/iqra_floating_planet/__init__.py`](./core/modules/intelligence/iqra_floating_planet/__init__.py.md)
- [`core/modules/intelligence/iqra_floating_planet/_chat_mixin.py`](./core/modules/intelligence/iqra_floating_planet/_chat_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet/_core.py`](./core/modules/intelligence/iqra_floating_planet/_core.py.md)
- [`core/modules/intelligence/iqra_floating_planet/_exit_mixin.py`](./core/modules/intelligence/iqra_floating_planet/_exit_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet/_modules_mixin.py`](./core/modules/intelligence/iqra_floating_planet/_modules_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet/floating_planet_anim_mixin.py`](./core/modules/intelligence/iqra_floating_planet/floating_planet_anim_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet/floating_planet_draw_mixin.py`](./core/modules/intelligence/iqra_floating_planet/floating_planet_draw_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet/floating_planet_menu_mixin.py`](./core/modules/intelligence/iqra_floating_planet/floating_planet_menu_mixin.py.md)
- [`core/modules/intelligence/iqra_floating_planet.py`](./core/modules/intelligence/iqra_floating_planet.py.md)
- [`core/modules/intelligence/json_tools.py`](./core/modules/intelligence/json_tools.py.md)
- [`core/modules/intelligence/key_manager.py`](./core/modules/intelligence/key_manager.py.md)
- [`core/modules/intelligence/knowledge_base.py`](./core/modules/intelligence/knowledge_base.py.md)
- [`core/modules/intelligence/marketing_tools/__init__.py`](./core/modules/intelligence/marketing_tools/__init__.py.md)
- [`core/modules/intelligence/marketing_tools/_core.py`](./core/modules/intelligence/marketing_tools/_core.py.md)
- [`core/modules/intelligence/marketing_tools/_registration.py`](./core/modules/intelligence/marketing_tools/_registration.py.md)
- [`core/modules/intelligence/marketing_tools.py`](./core/modules/intelligence/marketing_tools.py.md)
- [`core/modules/intelligence/model_config.py`](./core/modules/intelligence/model_config.py.md)
- [`core/modules/intelligence/monitor_dashboard.py`](./core/modules/intelligence/monitor_dashboard.py.md)
- [`core/modules/intelligence/offline_analyzer.py`](./core/modules/intelligence/offline_analyzer.py.md)
- [`core/modules/intelligence/password_tools.py`](./core/modules/intelligence/password_tools.py.md)
- [`core/modules/intelligence/performance_monitor.py`](./core/modules/intelligence/performance_monitor.py.md)
- [`core/modules/intelligence/predictor_window.py`](./core/modules/intelligence/predictor_window.py.md)
- [`core/modules/intelligence/quick_actions.py`](./core/modules/intelligence/quick_actions.py.md)
- [`core/modules/intelligence/quick_tools_panel/__init__.py`](./core/modules/intelligence/quick_tools_panel/__init__.py.md)
- [`core/modules/intelligence/quick_tools_panel/_api_config.py`](./core/modules/intelligence/quick_tools_panel/_api_config.py.md)
- [`core/modules/intelligence/quick_tools_panel/_quick_tools.py`](./core/modules/intelligence/quick_tools_panel/_quick_tools.py.md)
- [`core/modules/intelligence/quick_tools_panel.py`](./core/modules/intelligence/quick_tools_panel.py.md)
- [`core/modules/intelligence/rag_injector.py`](./core/modules/intelligence/rag_injector.py.md)
- [`core/modules/intelligence/recommendation_engine.py`](./core/modules/intelligence/recommendation_engine.py.md)
- [`core/modules/intelligence/report_generator.py`](./core/modules/intelligence/report_generator.py.md)
- [`core/modules/intelligence/sales_predictor.py`](./core/modules/intelligence/sales_predictor.py.md)
- [`core/modules/intelligence/scan_window.py`](./core/modules/intelligence/scan_window.py.md)
- [`core/modules/intelligence/screen_recorder.py`](./core/modules/intelligence/screen_recorder.py.md)
- [`core/modules/intelligence/self_monitor.py`](./core/modules/intelligence/self_monitor.py.md)
- [`core/modules/intelligence/session_context.py`](./core/modules/intelligence/session_context.py.md)
- [`core/modules/intelligence/smart_assistant.py`](./core/modules/intelligence/smart_assistant.py.md)
- [`core/modules/intelligence/smart_report_tools.py`](./core/modules/intelligence/smart_report_tools.py.md)
- [`core/modules/intelligence/smart_workflow.py`](./core/modules/intelligence/smart_workflow.py.md)
- [`core/modules/intelligence/solar_system_data/__init__.py`](./core/modules/intelligence/solar_system_data/__init__.py.md)
- [`core/modules/intelligence/solar_system_data/_catalog.py`](./core/modules/intelligence/solar_system_data/_catalog.py.md)
- [`core/modules/intelligence/solar_system_data/_core.py`](./core/modules/intelligence/solar_system_data/_core.py.md)
- [`core/modules/intelligence/solar_system_data/_data.py`](./core/modules/intelligence/solar_system_data/_data.py.md)
- [`core/modules/intelligence/solar_system_data.py`](./core/modules/intelligence/solar_system_data.py.md)
- [`core/modules/intelligence/solar_system_window.py`](./core/modules/intelligence/solar_system_window.py.md)
- [`core/modules/intelligence/super_intelligence.py`](./core/modules/intelligence/super_intelligence.py.md)
- [`core/modules/intelligence/system_hub_window.py`](./core/modules/intelligence/system_hub_window.py.md)
- [`core/modules/intelligence/system_monitor.py`](./core/modules/intelligence/system_monitor.py.md)
- [`core/modules/intelligence/text_editor/__init__.py`](./core/modules/intelligence/text_editor/__init__.py.md)
- [`core/modules/intelligence/text_editor/_core.py`](./core/modules/intelligence/text_editor/_core.py.md)
- [`core/modules/intelligence/text_editor/_crypto.py`](./core/modules/intelligence/text_editor/_crypto.py.md)
- [`core/modules/intelligence/text_editor/_note_tab.py`](./core/modules/intelligence/text_editor/_note_tab.py.md)
- [`core/modules/intelligence/text_editor.py`](./core/modules/intelligence/text_editor.py.md)
- [`core/modules/intelligence/timestamp_tools.py`](./core/modules/intelligence/timestamp_tools.py.md)
- [`core/modules/intelligence/tool_registry.py`](./core/modules/intelligence/tool_registry.py.md)
- [`core/modules/intelligence/tools_window.py`](./core/modules/intelligence/tools_window.py.md)
- [`core/modules/intelligence/usb_scanner.py`](./core/modules/intelligence/usb_scanner.py.md)
- [`core/modules/intelligence/vault_window.py`](./core/modules/intelligence/vault_window.py.md)
- [`core/modules/intelligence/voice_interface.py`](./core/modules/intelligence/voice_interface.py.md)
- [`core/modules/intelligence/whisper_recognizer.py`](./core/modules/intelligence/whisper_recognizer.py.md)
- [`core/modules/intelligence/window_top_tools.py`](./core/modules/intelligence/window_top_tools.py.md)
- [`core/modules/intelligence/workflow_engine/__init__.py`](./core/modules/intelligence/workflow_engine/__init__.py.md)
- [`core/modules/intelligence/workflow_engine/_engine.py`](./core/modules/intelligence/workflow_engine/_engine.py.md)
- [`core/modules/intelligence/workflow_engine/_models.py`](./core/modules/intelligence/workflow_engine/_models.py.md)
- [`core/modules/intelligence/workflow_engine.py`](./core/modules/intelligence/workflow_engine.py.md)
- [`core/modules/notification/notification_window.py`](./core/modules/notification/notification_window.py.md)
- [`core/modules/permission/permission_window.py`](./core/modules/permission/permission_window.py.md)
- [`core/modules/personnel/__init__.py`](./core/modules/personnel/__init__.py.md)
- [`core/modules/personnel/distribution_service.py`](./core/modules/personnel/distribution_service.py.md)
- [`core/modules/personnel/distribution_window/__init__.py`](./core/modules/personnel/distribution_window/__init__.py.md)
- [`core/modules/personnel/distribution_window/_commissions.py`](./core/modules/personnel/distribution_window/_commissions.py.md)
- [`core/modules/personnel/distribution_window/_dashboard.py`](./core/modules/personnel/distribution_window/_dashboard.py.md)
- [`core/modules/personnel/distribution_window/_links.py`](./core/modules/personnel/distribution_window/_links.py.md)
- [`core/modules/personnel/distribution_window/_stat_card.py`](./core/modules/personnel/distribution_window/_stat_card.py.md)
- [`core/modules/personnel/distribution_window/_team.py`](./core/modules/personnel/distribution_window/_team.py.md)
- [`core/modules/personnel/distribution_window/_ui.py`](./core/modules/personnel/distribution_window/_ui.py.md)
- [`core/modules/personnel/member_service.py`](./core/modules/personnel/member_service.py.md)
- [`core/modules/personnel/member_window.py`](./core/modules/personnel/member_window.py.md)
- [`core/modules/personnel/personnel_window.py`](./core/modules/personnel/personnel_window.py.md)
- [`core/modules/personnel/staff_service.py`](./core/modules/personnel/staff_service.py.md)
- [`core/modules/personnel/staff_window.py`](./core/modules/personnel/staff_window.py.md)
- [`core/modules/personnel/wallet_service/__init__.py`](./core/modules/personnel/wallet_service/__init__.py.md)
- [`core/modules/personnel/wallet_service/_address.py`](./core/modules/personnel/wallet_service/_address.py.md)
- [`core/modules/personnel/wallet_service/_cloud.py`](./core/modules/personnel/wallet_service/_cloud.py.md)
- [`core/modules/personnel/wallet_service/_db.py`](./core/modules/personnel/wallet_service/_db.py.md)
- [`core/modules/personnel/wallet_service/_transactions.py`](./core/modules/personnel/wallet_service/_transactions.py.md)
- [`core/modules/personnel/wallet_service/_wallet_crud.py`](./core/modules/personnel/wallet_service/_wallet_crud.py.md)
- [`core/modules/personnel/wallet_service/_withdrawal_queue.py`](./core/modules/personnel/wallet_service/_withdrawal_queue.py.md)
- [`core/modules/personnel/wallet_window/__init__.py`](./core/modules/personnel/wallet_window/__init__.py.md)
- [`core/modules/personnel/wallet_window/_address_book.py`](./core/modules/personnel/wallet_window/_address_book.py.md)
- [`core/modules/personnel/wallet_window/_batch_ops.py`](./core/modules/personnel/wallet_window/_batch_ops.py.md)
- [`core/modules/personnel/wallet_window/_dashboard_tab.py`](./core/modules/personnel/wallet_window/_dashboard_tab.py.md)
- [`core/modules/personnel/wallet_window/_dialogs.py`](./core/modules/personnel/wallet_window/_dialogs.py.md)
- [`core/modules/personnel/wallet_window/_stat_card.py`](./core/modules/personnel/wallet_window/_stat_card.py.md)
- [`core/modules/personnel/wallet_window/_transactions_tab.py`](./core/modules/personnel/wallet_window/_transactions_tab.py.md)
- [`core/modules/personnel/wallet_window/_wallets_tab.py`](./core/modules/personnel/wallet_window/_wallets_tab.py.md)
- [`core/modules/personnel/wallet_window/_withdrawal_tab.py`](./core/modules/personnel/wallet_window/_withdrawal_tab.py.md)
- [`core/modules/personnel/wallet_window.py`](./core/modules/personnel/wallet_window.py.md)
- [`core/modules/startup/startup_selector_window.py`](./core/modules/startup/startup_selector_window.py.md)
- [`core/modules/supabase/__init__.py`](./core/modules/supabase/__init__.py.md)
- [`core/modules/supabase/_core.py`](./core/modules/supabase/_core.py.md)
- [`core/modules/supabase/activation.py`](./core/modules/supabase/activation.py.md)
- [`core/modules/supabase/admin_log.py`](./core/modules/supabase/admin_log.py.md)
- [`core/modules/supabase/auth.py`](./core/modules/supabase/auth.py.md)
- [`core/modules/supabase/business.py`](./core/modules/supabase/business.py.md)
- [`core/modules/supabase/distribution.py`](./core/modules/supabase/distribution.py.md)
- [`core/modules/supabase/member.py`](./core/modules/supabase/member.py.md)
- [`core/modules/supabase/updater.py`](./core/modules/supabase/updater.py.md)
- [`core/modules/supabase/wallet.py`](./core/modules/supabase/wallet.py.md)
- [`core/modules/system/__init__.py`](./core/modules/system/__init__.py.md)
- [`core/modules/system/_archived/activation_window.py`](./core/modules/system/_archived/activation_window.py.md)
- [`core/modules/system/_archived/base_info_window.py`](./core/modules/system/_archived/base_info_window.py.md)
- [`core/modules/system/_archived/cloud_window.py`](./core/modules/system/_archived/cloud_window.py.md)
- [`core/modules/system/_archived/logs_window.py`](./core/modules/system/_archived/logs_window.py.md)
- [`core/modules/system/_archived/system_window.py`](./core/modules/system/_archived/system_window.py.md)
- [`core/modules/system/_archived/update_dialog.py`](./core/modules/system/_archived/update_dialog.py.md)
- [`core/modules/system/audit_window.py`](./core/modules/system/audit_window.py.md)
- [`core/modules/system/base_info_window.py`](./core/modules/system/base_info_window.py.md)
- [`core/modules/system/cloud_model_panel.py`](./core/modules/system/cloud_model_panel.py.md)
- [`core/modules/system/cloud_module.py`](./core/modules/system/cloud_module.py.md)
- [`core/modules/system/cloud_server_window.py`](./core/modules/system/cloud_server_window.py.md)
- [`core/modules/system/cloud_window.py`](./core/modules/system/cloud_window.py.md)
- [`core/modules/system/logs_window.py`](./core/modules/system/logs_window.py.md)
- [`core/modules/system/system_hub_window.py`](./core/modules/system/system_hub_window.py.md)
- [`core/modules/system/system_logs_service.py`](./core/modules/system/system_logs_service.py.md)
- [`core/modules/system_logs/system_logs_service.py`](./core/modules/system_logs/system_logs_service.py.md)
- [`core/modules/system_logs/system_logs_window.py`](./core/modules/system_logs/system_logs_window.py.md)
- [`core/modules/workflow/workflow_window.py`](./core/modules/workflow/workflow_window.py.md)
- [`core/notification_cron.py`](./core/notification_cron.py.md)
- [`core/notification_service.py`](./core/notification_service.py.md)
- [`core/notification_toast.py`](./core/notification_toast.py.md)
- [`core/obscura_provider.py`](./core/obscura_provider.py.md)
- [`core/operation_log.py`](./core/operation_log.py.md)
- [`core/oplog.py`](./core/oplog.py.md)
- [`core/patch_engine.py`](./core/patch_engine.py.md)
- [`core/paths.py`](./core/paths.py.md)
- [`core/planet_daemon.py`](./core/planet_daemon.py.md)
- [`core/planet_painter.py`](./core/planet_painter.py.md)
- [`core/procedural_texture.py`](./core/procedural_texture.py.md)
- [`core/reconciliation.py`](./core/reconciliation.py.md)
- [`core/rollback_control.py`](./core/rollback_control.py.md)
- [`core/scheduled_tasks.py`](./core/scheduled_tasks.py.md)
- [`core/services/__init__.py`](./core/services/__init__.py.md)
- [`core/services/ad_service.py`](./core/services/ad_service.py.md)
- [`core/services/ai_chatbot_service.py`](./core/services/ai_chatbot_service.py.md)
- [`core/services/audit_service.py`](./core/services/audit_service.py.md)
- [`core/services/backup_service.py`](./core/services/backup_service.py.md)
- [`core/services/backup_tool.py`](./core/services/backup_tool.py.md)
- [`core/services/barcode_service.py`](./core/services/barcode_service.py.md)
- [`core/services/bi_service.py`](./core/services/bi_service.py.md)
- [`core/services/cache_service.py`](./core/services/cache_service.py.md)
- [`core/services/chart_service.py`](./core/services/chart_service.py.md)
- [`core/services/database_optimizer.py`](./core/services/database_optimizer.py.md)
- [`core/services/encryption_service.py`](./core/services/encryption_service.py.md)
- [`core/services/export_service.py`](./core/services/export_service.py.md)
- [`core/services/hotkey_manager.py`](./core/services/hotkey_manager.py.md)
- [`core/services/i18n_service.py`](./core/services/i18n_service.py.md)
- [`core/services/image_cache_service.py`](./core/services/image_cache_service.py.md)
- [`core/services/import_export_service.py`](./core/services/import_export_service.py.md)
- [`core/services/lazy_load_service.py`](./core/services/lazy_load_service.py.md)
- [`core/services/license_service.py`](./core/services/license_service.py.md)
- [`core/services/logistics_service.py`](./core/services/logistics_service.py.md)
- [`core/services/memory_service.py`](./core/services/memory_service.py.md)
- [`core/services/nl_query_service.py`](./core/services/nl_query_service.py.md)
- [`core/services/notification_service.py`](./core/services/notification_service.py.md)
- [`core/services/offline_queue.py`](./core/services/offline_queue.py.md)
- [`core/services/payment_service.py`](./core/services/payment_service.py.md)
- [`core/services/performance_service.py`](./core/services/performance_service.py.md)
- [`core/services/permission_service.py`](./core/services/permission_service.py.md)
- [`core/services/print_service.py`](./core/services/print_service.py.md)
- [`core/services/realtime_service.py`](./core/services/realtime_service.py.md)
- [`core/services/sales_prediction_service.py`](./core/services/sales_prediction_service.py.md)
- [`core/services/scheduler_service.py`](./core/services/scheduler_service.py.md)
- [`core/services/sms_service.py`](./core/services/sms_service.py.md)
- [`core/services/sync_manager.py`](./core/services/sync_manager.py.md)
- [`core/services/system_service.py`](./core/services/system_service.py.md)
- [`core/services/system_tray.py`](./core/services/system_tray.py.md)
- [`core/services/template_service.py`](./core/services/template_service.py.md)
- [`core/services/theme_service.py`](./core/services/theme_service.py.md)
- [`core/services/update_service.py`](./core/services/update_service.py.md)
- [`core/services/workflow_service.py`](./core/services/workflow_service.py.md)
- [`core/shapes/__init__.py`](./core/shapes/__init__.py.md)
- [`core/shapes/alien.py`](./core/shapes/alien.py.md)
- [`core/shapes/black_hole.py`](./core/shapes/black_hole.py.md)
- [`core/shapes/classic.py`](./core/shapes/classic.py.md)
- [`core/shapes/classic_20260614_184255_598.py`](./core/shapes/classic_20260614_184255_598.py.md)
- [`core/shapes/comet.py`](./core/shapes/comet.py.md)
- [`core/shapes/corvette.py`](./core/shapes/corvette.py.md)
- [`core/shapes/crystal_alien.py`](./core/shapes/crystal_alien.py.md)
- [`core/shapes/destroyer.py`](./core/shapes/destroyer.py.md)
- [`core/shapes/dreadnought.py`](./core/shapes/dreadnought.py.md)
- [`core/shapes/energy_being.py`](./core/shapes/energy_being.py.md)
- [`core/shapes/fighter.py`](./core/shapes/fighter.py.md)
- [`core/shapes/gas_giant.py`](./core/shapes/gas_giant.py.md)
- [`core/shapes/gas_giant_20260614_184255_426.py`](./core/shapes/gas_giant_20260614_184255_426.py.md)
- [`core/shapes/ghost_alien.py`](./core/shapes/ghost_alien.py.md)
- [`core/shapes/grey_alien.py`](./core/shapes/grey_alien.py.md)
- [`core/shapes/ice_giant.py`](./core/shapes/ice_giant.py.md)
- [`core/shapes/ice_giant_20260614_184255_207.py`](./core/shapes/ice_giant_20260614_184255_207.py.md)
- [`core/shapes/interceptor.py`](./core/shapes/interceptor.py.md)
- [`core/shapes/jellyfish_alien.py`](./core/shapes/jellyfish_alien.py.md)
- [`core/shapes/lava_planet.py`](./core/shapes/lava_planet.py.md)
- [`core/shapes/lava_planet_20260614_184255_101.py`](./core/shapes/lava_planet_20260614_184255_101.py.md)
- [`core/shapes/mars.py`](./core/shapes/mars.py.md)
- [`core/shapes/mars_20260614_184255_257.py`](./core/shapes/mars_20260614_184255_257.py.md)
- [`core/shapes/mercury.py`](./core/shapes/mercury.py.md)
- [`core/shapes/nebula.py`](./core/shapes/nebula.py.md)
- [`core/shapes/neutron_star.py`](./core/shapes/neutron_star.py.md)
- [`core/shapes/octopus_alien.py`](./core/shapes/octopus_alien.py.md)
- [`core/shapes/pluto.py`](./core/shapes/pluto.py.md)
- [`core/shapes/pulsar.py`](./core/shapes/pulsar.py.md)
- [`core/shapes/red_giant.py`](./core/shapes/red_giant.py.md)
- [`core/shapes/reptilian.py`](./core/shapes/reptilian.py.md)
- [`core/shapes/robot_alien.py`](./core/shapes/robot_alien.py.md)
- [`core/shapes/saturn.py`](./core/shapes/saturn.py.md)
- [`core/shapes/scout.py`](./core/shapes/scout.py.md)
- [`core/shapes/starship.py`](./core/shapes/starship.py.md)
- [`core/shapes/transporter.py`](./core/shapes/transporter.py.md)
- [`core/shapes/uranus.py`](./core/shapes/uranus.py.md)
- [`core/shapes/venus.py`](./core/shapes/venus.py.md)
- [`core/shapes/white_dwarf.py`](./core/shapes/white_dwarf.py.md)
- [`core/shapes/wormhole.py`](./core/shapes/wormhole.py.md)
- [`core/simple_sync.py`](./core/simple_sync.py.md)
- [`core/siri_command_handler.py`](./core/siri_command_handler.py.md)
- [`core/smart_memory_adapter.py`](./core/smart_memory_adapter.py.md)
- [`core/smart_report.py`](./core/smart_report.py.md)
- [`core/storage.py`](./core/storage.py.md)
- [`core/supabase_client.py`](./core/supabase_client.py.md)
- [`core/sync_bridge.py`](./core/sync_bridge.py.md)
- [`core/sync_decorator.py`](./core/sync_decorator.py.md)
- [`core/sync_integration.py`](./core/sync_integration.py.md)
- [`core/sync_manager.py`](./core/sync_manager.py.md)
- [`core/task_scheduler.py`](./core/task_scheduler.py.md)
- [`core/tests/conftest.py`](./core/tests/conftest.py.md)
- [`core/texture_mapper.py`](./core/texture_mapper.py.md)
- [`core/theme.py`](./core/theme.py.md)
- [`core/tool_registry.py`](./core/tool_registry.py.md)
- [`core/tools/__init__.py`](./core/tools/__init__.py.md)
- [`core/tools/environments/__init__.py`](./core/tools/environments/__init__.py.md)
- [`core/tools/environments/file_sync.py`](./core/tools/environments/file_sync.py.md)
- [`core/tools/skills_sync.py`](./core/tools/skills_sync.py.md)
- [`core/ui_components.py`](./core/ui_components.py.md)
- [`core/user_dao.py`](./core/user_dao.py.md)
- [`core/voice.py`](./core/voice.py.md)
- [`core/workflow_engine.py`](./core/workflow_engine.py.md)
- [`core/workspace_indexer.py`](./core/workspace_indexer.py.md)
- [`gen_book.py`](./gen_book.py.md)
- [`iqra/_archived/dedup_20260619_170800/deps.py`](./iqra/_archived/dedup_20260619_170800/deps.py.md)
- [`iqra/_archived/license_模块归档_20260619/license_crypto.py`](./iqra/_archived/license_模块归档_20260619/license_crypto.py.md)
- [`iqra/_archived/license_模块归档_20260619/license_db.py`](./iqra/_archived/license_模块归档_20260619/license_db.py.md)
- [`iqra/_archived/license_模块归档_20260619/license_service.py`](./iqra/_archived/license_模块归档_20260619/license_service.py.md)
- [`iqra/config/__init__.py`](./iqra/config/__init__.py.md)
- [`iqra/config/supabase_config.py`](./iqra/config/supabase_config.py.md)
- [`iqra/core/__init__.py`](./iqra/core/__init__.py.md)
- [`iqra/core/_agent_events.py`](./iqra/core/_agent_events.py.md)
- [`iqra/core/_agent_fallbacks.py`](./iqra/core/_agent_fallbacks.py.md)
- [`iqra/core/_agent_loop_base.py`](./iqra/core/_agent_loop_base.py.md)
- [`iqra/core/_agent_loop_compat_mixin.py`](./iqra/core/_agent_loop_compat_mixin.py.md)
- [`iqra/core/_agent_loop_exec_mixin.py`](./iqra/core/_agent_loop_exec_mixin.py.md)
- [`iqra/core/_agent_prompts.py`](./iqra/core/_agent_prompts.py.md)
- [`iqra/core/_backend_convenience.py`](./iqra/core/_backend_convenience.py.md)
- [`iqra/core/_backend_factory.py`](./iqra/core/_backend_factory.py.md)
- [`iqra/core/_backend_models.py`](./iqra/core/_backend_models.py.md)
- [`iqra/core/_backend_providers.py`](./iqra/core/_backend_providers.py.md)
- [`iqra/core/_backend_utils.py`](./iqra/core/_backend_utils.py.md)
- [`iqra/core/_base_backend.py`](./iqra/core/_base_backend.py.md)
- [`iqra/core/_basic_tools.py`](./iqra/core/_basic_tools.py.md)
- [`iqra/core/_bm25.py`](./iqra/core/_bm25.py.md)
- [`iqra/core/_chunker.py`](./iqra/core/_chunker.py.md)
- [`iqra/core/_claude_tools.py`](./iqra/core/_claude_tools.py.md)
- [`iqra/core/_config_helpers.py`](./iqra/core/_config_helpers.py.md)
- [`iqra/core/_deprecated/cloud_sync_v2.py`](./iqra/core/_deprecated/cloud_sync_v2.py.md)
- [`iqra/core/_index_config.py`](./iqra/core/_index_config.py.md)
- [`iqra/core/_index_models.py`](./iqra/core/_index_models.py.md)
- [`iqra/core/_quick_funcs.py`](./iqra/core/_quick_funcs.py.md)
- [`iqra/core/_test_llm_decompose.py`](./iqra/core/_test_llm_decompose.py.md)
- [`iqra/core/_tokenizer.py`](./iqra/core/_tokenizer.py.md)
- [`iqra/core/_tool_registry.py`](./iqra/core/_tool_registry.py.md)
- [`iqra/core/ad_launcher.py`](./iqra/core/ad_launcher.py.md)
- [`iqra/core/agent.py`](./iqra/core/agent.py.md)
- [`iqra/core/agent_delegate.py`](./iqra/core/agent_delegate.py.md)
- [`iqra/core/agent_delegate_adapter.py`](./iqra/core/agent_delegate_adapter.py.md)
- [`iqra/core/agent_loop.py`](./iqra/core/agent_loop.py.md)
- [`iqra/core/app_state.py`](./iqra/core/app_state.py.md)
- [`iqra/core/auth_service.py`](./iqra/core/auth_service.py.md)
- [`iqra/core/backup.py`](./iqra/core/backup.py.md)
- [`iqra/core/book_search.py`](./iqra/core/book_search.py.md)
- [`iqra/core/business_service.py`](./iqra/core/business_service.py.md)
- [`iqra/core/ceo_agent.py`](./iqra/core/ceo_agent.py.md)
- [`iqra/core/chat_engine.py`](./iqra/core/chat_engine.py.md)
- [`iqra/core/clarify_system.py`](./iqra/core/clarify_system.py.md)
- [`iqra/core/cloud_pull.py`](./iqra/core/cloud_pull.py.md)
- [`iqra/core/cloud_sync.py`](./iqra/core/cloud_sync.py.md)
- [`iqra/core/code_executor.py`](./iqra/core/code_executor.py.md)
- [`iqra/core/code_intel.py`](./iqra/core/code_intel.py.md)
- [`iqra/core/collaboration_client.py`](./iqra/core/collaboration_client.py.md)
- [`iqra/core/config_validator.py`](./iqra/core/config_validator.py.md)
- [`iqra/core/conflict_resolver.py`](./iqra/core/conflict_resolver.py.md)
- [`iqra/core/core_engine.py`](./iqra/core/core_engine.py.md)
- [`iqra/core/cosmic.py`](./iqra/core/cosmic.py.md)
- [`iqra/core/custom_fields.py`](./iqra/core/custom_fields.py.md)
- [`iqra/core/dark_theme.py`](./iqra/core/dark_theme.py.md)
- [`iqra/core/dark_tool_theme.py`](./iqra/core/dark_tool_theme.py.md)
- [`iqra/core/data.py`](./iqra/core/data.py.md)
- [`iqra/core/data_sync.py`](./iqra/core/data_sync.py.md)
- [`iqra/core/database.py`](./iqra/core/database.py.md)
- [`iqra/core/enhanced_core.py`](./iqra/core/enhanced_core.py.md)
- [`iqra/core/event_bus.py`](./iqra/core/event_bus.py.md)
- [`iqra/core/excel_export.py`](./iqra/core/excel_export.py.md)
- [`iqra/core/git_ops.py`](./iqra/core/git_ops.py.md)
- [`iqra/core/harness/__init__.py`](./iqra/core/harness/__init__.py.md)
- [`iqra/core/harness/config_schema.py`](./iqra/core/harness/config_schema.py.md)
- [`iqra/core/iqra_logging.py`](./iqra/core/iqra_logging.py.md)
- [`iqra/core/light_tool_theme.py`](./iqra/core/light_tool_theme.py.md)
- [`iqra/core/llm_backend.py`](./iqra/core/llm_backend.py.md)
- [`iqra/core/llm_client.py`](./iqra/core/llm_client.py.md)
- [`iqra/core/machine_code.py`](./iqra/core/machine_code.py.md)
- [`iqra/core/memory.py`](./iqra/core/memory.py.md)
- [`iqra/core/memory_store.py`](./iqra/core/memory_store.py.md)
- [`iqra/core/mobile_api.py`](./iqra/core/mobile_api.py.md)
- [`iqra/core/model_status.py`](./iqra/core/model_status.py.md)
- [`iqra/core/model_status_manager.py`](./iqra/core/model_status_manager.py.md)
- [`iqra/core/module_manager.py`](./iqra/core/module_manager.py.md)
- [`iqra/core/modules/__init__.py`](./iqra/core/modules/__init__.py.md)
- [`iqra/core/modules/supabase/__init__.py`](./iqra/core/modules/supabase/__init__.py.md)
- [`iqra/core/modules/supabase/_core.py`](./iqra/core/modules/supabase/_core.py.md)
- [`iqra/core/modules/supabase/activation.py`](./iqra/core/modules/supabase/activation.py.md)
- [`iqra/core/modules/supabase/admin_log.py`](./iqra/core/modules/supabase/admin_log.py.md)
- [`iqra/core/modules/supabase/auth.py`](./iqra/core/modules/supabase/auth.py.md)
- [`iqra/core/modules/supabase/business.py`](./iqra/core/modules/supabase/business.py.md)
- [`iqra/core/modules/supabase/distribution.py`](./iqra/core/modules/supabase/distribution.py.md)
- [`iqra/core/modules/supabase/member.py`](./iqra/core/modules/supabase/member.py.md)
- [`iqra/core/modules/supabase/updater.py`](./iqra/core/modules/supabase/updater.py.md)
- [`iqra/core/modules/supabase/wallet.py`](./iqra/core/modules/supabase/wallet.py.md)
- [`iqra/core/multi_model.py`](./iqra/core/multi_model.py.md)
- [`iqra/core/multi_model_chat_engine.py`](./iqra/core/multi_model_chat_engine.py.md)
- [`iqra/core/notification_cron.py`](./iqra/core/notification_cron.py.md)
- [`iqra/core/notification_service.py`](./iqra/core/notification_service.py.md)
- [`iqra/core/notification_toast.py`](./iqra/core/notification_toast.py.md)
- [`iqra/core/obscura_provider.py`](./iqra/core/obscura_provider.py.md)
- [`iqra/core/observability/__init__.py`](./iqra/core/observability/__init__.py.md)
- [`iqra/core/observability/cost_tracker.py`](./iqra/core/observability/cost_tracker.py.md)
- [`iqra/core/observability/schema.py`](./iqra/core/observability/schema.py.md)
- [`iqra/core/observability/token_observer.py`](./iqra/core/observability/token_observer.py.md)
- [`iqra/core/observability/trace_manager.py`](./iqra/core/observability/trace_manager.py.md)
- [`iqra/core/operation_log.py`](./iqra/core/operation_log.py.md)
- [`iqra/core/oplog.py`](./iqra/core/oplog.py.md)
- [`iqra/core/patch_engine.py`](./iqra/core/patch_engine.py.md)
- [`iqra/core/paths.py`](./iqra/core/paths.py.md)
- [`iqra/core/performance_monitor.py`](./iqra/core/performance_monitor.py.md)
- [`iqra/core/planet_painter.py`](./iqra/core/planet_painter.py.md)
- [`iqra/core/proactive_engine.py`](./iqra/core/proactive_engine.py.md)
- [`iqra/core/proactive_monitors.py`](./iqra/core/proactive_monitors.py.md)
- [`iqra/core/procedural_texture.py`](./iqra/core/procedural_texture.py.md)
- [`iqra/core/process_manager.py`](./iqra/core/process_manager.py.md)
- [`iqra/core/prompts/__init__.py`](./iqra/core/prompts/__init__.py.md)
- [`iqra/core/prompts/task_decompose.py`](./iqra/core/prompts/task_decompose.py.md)
- [`iqra/core/provider_registry.py`](./iqra/core/provider_registry.py.md)
- [`iqra/core/rag_context.py`](./iqra/core/rag_context.py.md)
- [`iqra/core/reconciliation.py`](./iqra/core/reconciliation.py.md)
- [`iqra/core/scheduled_tasks.py`](./iqra/core/scheduled_tasks.py.md)
- [`iqra/core/secure_storage.py`](./iqra/core/secure_storage.py.md)
- [`iqra/core/semantic_search.py`](./iqra/core/semantic_search.py.md)
- [`iqra/core/session_search.py`](./iqra/core/session_search.py.md)
- [`iqra/core/shapes/__init__.py`](./iqra/core/shapes/__init__.py.md)
- [`iqra/core/shapes/alien.py`](./iqra/core/shapes/alien.py.md)
- [`iqra/core/shapes/black_hole.py`](./iqra/core/shapes/black_hole.py.md)
- [`iqra/core/shapes/classic.py`](./iqra/core/shapes/classic.py.md)
- [`iqra/core/shapes/comet.py`](./iqra/core/shapes/comet.py.md)
- [`iqra/core/shapes/corvette.py`](./iqra/core/shapes/corvette.py.md)
- [`iqra/core/shapes/crystal_alien.py`](./iqra/core/shapes/crystal_alien.py.md)
- [`iqra/core/shapes/destroyer.py`](./iqra/core/shapes/destroyer.py.md)
- [`iqra/core/shapes/dreadnought.py`](./iqra/core/shapes/dreadnought.py.md)
- [`iqra/core/shapes/energy_being.py`](./iqra/core/shapes/energy_being.py.md)
- [`iqra/core/shapes/fighter.py`](./iqra/core/shapes/fighter.py.md)
- [`iqra/core/shapes/gas_giant.py`](./iqra/core/shapes/gas_giant.py.md)
- [`iqra/core/shapes/ghost_alien.py`](./iqra/core/shapes/ghost_alien.py.md)
- [`iqra/core/shapes/grey_alien.py`](./iqra/core/shapes/grey_alien.py.md)
- [`iqra/core/shapes/ice_giant.py`](./iqra/core/shapes/ice_giant.py.md)
- [`iqra/core/shapes/interceptor.py`](./iqra/core/shapes/interceptor.py.md)
- [`iqra/core/shapes/jellyfish_alien.py`](./iqra/core/shapes/jellyfish_alien.py.md)
- [`iqra/core/shapes/lava_planet.py`](./iqra/core/shapes/lava_planet.py.md)
- [`iqra/core/shapes/mars.py`](./iqra/core/shapes/mars.py.md)
- [`iqra/core/shapes/mercury.py`](./iqra/core/shapes/mercury.py.md)
- [`iqra/core/shapes/nebula.py`](./iqra/core/shapes/nebula.py.md)
- [`iqra/core/shapes/neutron_star.py`](./iqra/core/shapes/neutron_star.py.md)
- [`iqra/core/shapes/octopus_alien.py`](./iqra/core/shapes/octopus_alien.py.md)
- [`iqra/core/shapes/pluto.py`](./iqra/core/shapes/pluto.py.md)
- [`iqra/core/shapes/pulsar.py`](./iqra/core/shapes/pulsar.py.md)
- [`iqra/core/shapes/red_giant.py`](./iqra/core/shapes/red_giant.py.md)
- [`iqra/core/shapes/reptilian.py`](./iqra/core/shapes/reptilian.py.md)
- [`iqra/core/shapes/robot_alien.py`](./iqra/core/shapes/robot_alien.py.md)
- [`iqra/core/shapes/saturn.py`](./iqra/core/shapes/saturn.py.md)
- [`iqra/core/shapes/scout.py`](./iqra/core/shapes/scout.py.md)
- [`iqra/core/shapes/starship.py`](./iqra/core/shapes/starship.py.md)
- [`iqra/core/shapes/transporter.py`](./iqra/core/shapes/transporter.py.md)
- [`iqra/core/shapes/uranus.py`](./iqra/core/shapes/uranus.py.md)
- [`iqra/core/shapes/venus.py`](./iqra/core/shapes/venus.py.md)
- [`iqra/core/shapes/white_dwarf.py`](./iqra/core/shapes/white_dwarf.py.md)
- [`iqra/core/shapes/wormhole.py`](./iqra/core/shapes/wormhole.py.md)
- [`iqra/core/simple_sync.py`](./iqra/core/simple_sync.py.md)
- [`iqra/core/skill_loader.py`](./iqra/core/skill_loader.py.md)
- [`iqra/core/skill_system.py`](./iqra/core/skill_system.py.md)
- [`iqra/core/smart_memory.py`](./iqra/core/smart_memory.py.md)
- [`iqra/core/smart_memory_adapter.py`](./iqra/core/smart_memory_adapter.py.md)
- [`iqra/core/smart_report.py`](./iqra/core/smart_report.py.md)
- [`iqra/core/storage.py`](./iqra/core/storage.py.md)
- [`iqra/core/supabase_client.py`](./iqra/core/supabase_client.py.md)
- [`iqra/core/super_intelligence.py`](./iqra/core/super_intelligence.py.md)
- [`iqra/core/sync_bridge.py`](./iqra/core/sync_bridge.py.md)
- [`iqra/core/sync_decorator.py`](./iqra/core/sync_decorator.py.md)
- [`iqra/core/sync_integration.py`](./iqra/core/sync_integration.py.md)
- [`iqra/core/sync_manager.py`](./iqra/core/sync_manager.py.md)
- [`iqra/core/sync_optimized.py`](./iqra/core/sync_optimized.py.md)
- [`iqra/core/task_decomposer.py`](./iqra/core/task_decomposer.py.md)
- [`iqra/core/task_scheduler.py`](./iqra/core/task_scheduler.py.md)
- [`iqra/core/texture_mapper.py`](./iqra/core/texture_mapper.py.md)
- [`iqra/core/todo_system.py`](./iqra/core/todo_system.py.md)
- [`iqra/core/token_optimizer.py`](./iqra/core/token_optimizer.py.md)
- [`iqra/core/token_saver.py`](./iqra/core/token_saver.py.md)
- [`iqra/core/tool_registry.py`](./iqra/core/tool_registry.py.md)
- [`iqra/core/triple_sync.py`](./iqra/core/triple_sync.py.md)
- [`iqra/core/ui_components.py`](./iqra/core/ui_components.py.md)
- [`iqra/core/user_dao.py`](./iqra/core/user_dao.py.md)
- [`iqra/core/voice.py`](./iqra/core/voice.py.md)
- [`iqra/core/web_search.py`](./iqra/core/web_search.py.md)
- [`iqra/core/workflow_engine.py`](./iqra/core/workflow_engine.py.md)
- [`iqra/core/workspace_indexer.py`](./iqra/core/workspace_indexer.py.md)
- [`iqra/hermes_constants.py`](./iqra/hermes_constants.py.md)
- [`iqra/iqra_chat.py`](./iqra/iqra_chat.py.md)
- [`iqra/iqra_setup.py`](./iqra/iqra_setup.py.md)
- [`iqra/main.py`](./iqra/main.py.md)
- [`iqra/modules/__init__.py`](./iqra/modules/__init__.py.md)
- [`iqra/modules/auth/__init__.py`](./iqra/modules/auth/__init__.py.md)
- [`iqra/modules/auth/activation_gate.py`](./iqra/modules/auth/activation_gate.py.md)
- [`iqra/modules/auth/admin_login_dialog.py`](./iqra/modules/auth/admin_login_dialog.py.md)
- [`iqra/modules/auth/auth_service.py`](./iqra/modules/auth/auth_service.py.md)
- [`iqra/modules/auth/auth_service_membership.py`](./iqra/modules/auth/auth_service_membership.py.md)
- [`iqra/modules/auth/auth_service_sync.py`](./iqra/modules/auth/auth_service_sync.py.md)
- [`iqra/modules/auth/change_password_dialog.py`](./iqra/modules/auth/change_password_dialog.py.md)
- [`iqra/modules/auth/connect_window.py`](./iqra/modules/auth/connect_window.py.md)
- [`iqra/modules/auth/dao/user_dao.py`](./iqra/modules/auth/dao/user_dao.py.md)
- [`iqra/modules/auth/login_window.py`](./iqra/modules/auth/login_window.py.md)
- [`iqra/modules/auth/model_config_panel/__init__.py`](./iqra/modules/auth/model_config_panel/__init__.py.md)
- [`iqra/modules/auth/model_config_panel/_constants.py`](./iqra/modules/auth/model_config_panel/_constants.py.md)
- [`iqra/modules/auth/model_config_panel/_dialog.py`](./iqra/modules/auth/model_config_panel/_dialog.py.md)
- [`iqra/modules/auth/model_config_panel/_panel_config.py`](./iqra/modules/auth/model_config_panel/_panel_config.py.md)
- [`iqra/modules/auth/model_config_panel/_panel_custom.py`](./iqra/modules/auth/model_config_panel/_panel_custom.py.md)
- [`iqra/modules/auth/model_config_panel/_panel_local.py`](./iqra/modules/auth/model_config_panel/_panel_local.py.md)
- [`iqra/modules/auth/model_config_panel/_panel_preset.py`](./iqra/modules/auth/model_config_panel/_panel_preset.py.md)
- [`iqra/modules/auth/model_config_panel/_panel_ui.py`](./iqra/modules/auth/model_config_panel/_panel_ui.py.md)
- [`iqra/modules/auth/model_config_panel/_workers.py`](./iqra/modules/auth/model_config_panel/_workers.py.md)
- [`iqra/modules/auth/model_setup_window.py`](./iqra/modules/auth/model_setup_window.py.md)
- [`iqra/modules/auth/register_window.py`](./iqra/modules/auth/register_window.py.md)
- [`iqra/modules/auth/select_mode_window.py`](./iqra/modules/auth/select_mode_window.py.md)
- [`iqra/modules/auth/service/cloud_api.py`](./iqra/modules/auth/service/cloud_api.py.md)
- [`iqra/modules/auth/upgrade_window.py`](./iqra/modules/auth/upgrade_window.py.md)
- [`iqra/modules/dashboard/dashboard_window/__init__.py`](./iqra/modules/dashboard/dashboard_window/__init__.py.md)
- [`iqra/modules/dashboard/dashboard_window/_account_tools.py`](./iqra/modules/dashboard/dashboard_window/_account_tools.py.md)
- [`iqra/modules/dashboard/dashboard_window/_module_navigator.py`](./iqra/modules/dashboard/dashboard_window/_module_navigator.py.md)
- [`iqra/modules/dashboard/dashboard_window/_module_window.py`](./iqra/modules/dashboard/dashboard_window/_module_window.py.md)
- [`iqra/modules/dashboard/dashboard_window/_planets.py`](./iqra/modules/dashboard/dashboard_window/_planets.py.md)
- [`iqra/modules/dashboard/dashboard_window/_renderer.py`](./iqra/modules/dashboard/dashboard_window/_renderer.py.md)
- [`iqra/modules/dashboard/dashboard_window/_ui.py`](./iqra/modules/dashboard/dashboard_window/_ui.py.md)
- [`iqra/modules/dashboard/dashboard_window.py`](./iqra/modules/dashboard/dashboard_window.py.md)
- [`iqra/modules/intelligence/__init__.py`](./iqra/modules/intelligence/__init__.py.md)
- [`iqra/modules/intelligence/_ai_shared.py`](./iqra/modules/intelligence/_ai_shared.py.md)
- [`iqra/modules/intelligence/_ai_widgets.py`](./iqra/modules/intelligence/_ai_widgets.py.md)
- [`iqra/modules/intelligence/_ai_widgets_anomaly.py`](./iqra/modules/intelligence/_ai_widgets_anomaly.py.md)
- [`iqra/modules/intelligence/_ai_widgets_business.py`](./iqra/modules/intelligence/_ai_widgets_business.py.md)
- [`iqra/modules/intelligence/_ai_widgets_core.py`](./iqra/modules/intelligence/_ai_widgets_core.py.md)
- [`iqra/modules/intelligence/_ai_widgets_recommendation.py`](./iqra/modules/intelligence/_ai_widgets_recommendation.py.md)
- [`iqra/modules/intelligence/_ai_widgets_visualization.py`](./iqra/modules/intelligence/_ai_widgets_visualization.py.md)
- [`iqra/modules/intelligence/_ai_widgets_workflow.py`](./iqra/modules/intelligence/_ai_widgets_workflow.py.md)
- [`iqra/modules/intelligence/_api_key_dialog.py`](./iqra/modules/intelligence/_api_key_dialog.py.md)
- [`iqra/modules/intelligence/_chat_dialog.py`](./iqra/modules/intelligence/_chat_dialog.py.md)
- [`iqra/modules/intelligence/_compat.py`](./iqra/modules/intelligence/_compat.py.md)
- [`iqra/modules/intelligence/_floating_planet_chat_mixin.py`](./iqra/modules/intelligence/_floating_planet_chat_mixin.py.md)
- [`iqra/modules/intelligence/_floating_planet_input_mixin.py`](./iqra/modules/intelligence/_floating_planet_input_mixin.py.md)
- [`iqra/modules/intelligence/_floating_planet_modules_mixin.py`](./iqra/modules/intelligence/_floating_planet_modules_mixin.py.md)
- [`iqra/modules/intelligence/_model_manager.py`](./iqra/modules/intelligence/_model_manager.py.md)
- [`iqra/modules/intelligence/_model_manager_download.py`](./iqra/modules/intelligence/_model_manager_download.py.md)
- [`iqra/modules/intelligence/_model_manager_ollama.py`](./iqra/modules/intelligence/_model_manager_ollama.py.md)
- [`iqra/modules/intelligence/_navigation_hud.py`](./iqra/modules/intelligence/_navigation_hud.py.md)
- [`iqra/modules/intelligence/_quick_tools_widget.py`](./iqra/modules/intelligence/_quick_tools_widget.py.md)
- [`iqra/modules/intelligence/_shell_dialogs.py`](./iqra/modules/intelligence/_shell_dialogs.py.md)
- [`iqra/modules/intelligence/_stubs.py`](./iqra/modules/intelligence/_stubs.py.md)
- [`iqra/modules/intelligence/_text_crypto.py`](./iqra/modules/intelligence/_text_crypto.py.md)
- [`iqra/modules/intelligence/_text_editor_files_mixin.py`](./iqra/modules/intelligence/_text_editor_files_mixin.py.md)
- [`iqra/modules/intelligence/_text_editor_format_mixin.py`](./iqra/modules/intelligence/_text_editor_format_mixin.py.md)
- [`iqra/modules/intelligence/_text_editor_tree_mixin.py`](./iqra/modules/intelligence/_text_editor_tree_mixin.py.md)
- [`iqra/modules/intelligence/_text_editor_ui_mixin.py`](./iqra/modules/intelligence/_text_editor_ui_mixin.py.md)
- [`iqra/modules/intelligence/account_window.py`](./iqra/modules/intelligence/account_window.py.md)
- [`iqra/modules/intelligence/agent_bridge.py`](./iqra/modules/intelligence/agent_bridge.py.md)
- [`iqra/modules/intelligence/agent_bridge_models.py`](./iqra/modules/intelligence/agent_bridge_models.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/__init__.py`](./iqra/modules/intelligence/agent_bridge_tools/__init__.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_code_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_code_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_file_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_file_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_legacy_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_legacy_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_system_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_system_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_task_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_task_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools/_web_tools.py`](./iqra/modules/intelligence/agent_bridge_tools/_web_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_tools.py`](./iqra/modules/intelligence/agent_bridge_tools.py.md)
- [`iqra/modules/intelligence/agent_bridge_workers.py`](./iqra/modules/intelligence/agent_bridge_workers.py.md)
- [`iqra/modules/intelligence/ai_assistant_window.py`](./iqra/modules/intelligence/ai_assistant_window.py.md)
- [`iqra/modules/intelligence/ai_center_window.py`](./iqra/modules/intelligence/ai_center_window.py.md)
- [`iqra/modules/intelligence/ai_chat_styles.py`](./iqra/modules/intelligence/ai_chat_styles.py.md)
- [`iqra/modules/intelligence/ai_chat_window/__init__.py`](./iqra/modules/intelligence/ai_chat_window/__init__.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_chat_stream.py`](./iqra/modules/intelligence/ai_chat_window/_chat_stream.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_file_upload.py`](./iqra/modules/intelligence/ai_chat_window/_file_upload.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_misc.py`](./iqra/modules/intelligence/ai_chat_window/_misc.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_model_selector.py`](./iqra/modules/intelligence/ai_chat_window/_model_selector.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_session.py`](./iqra/modules/intelligence/ai_chat_window/_session.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_ui.py`](./iqra/modules/intelligence/ai_chat_window/_ui.py.md)
- [`iqra/modules/intelligence/ai_chat_window/_voice.py`](./iqra/modules/intelligence/ai_chat_window/_voice.py.md)
- [`iqra/modules/intelligence/ai_chat_window.py`](./iqra/modules/intelligence/ai_chat_window.py.md)
- [`iqra/modules/intelligence/ai_dashboard_window.py`](./iqra/modules/intelligence/ai_dashboard_window.py.md)
- [`iqra/modules/intelligence/ai_features_ai_dashboard.py`](./iqra/modules/intelligence/ai_features_ai_dashboard.py.md)
- [`iqra/modules/intelligence/ai_features_customer_ai.py`](./iqra/modules/intelligence/ai_features_customer_ai.py.md)
- [`iqra/modules/intelligence/ai_features_inventory_ai.py`](./iqra/modules/intelligence/ai_features_inventory_ai.py.md)
- [`iqra/modules/intelligence/ai_features_pricing_ai.py`](./iqra/modules/intelligence/ai_features_pricing_ai.py.md)
- [`iqra/modules/intelligence/ai_features_sales_ai.py`](./iqra/modules/intelligence/ai_features_sales_ai.py.md)
- [`iqra/modules/intelligence/analysis_tools.py`](./iqra/modules/intelligence/analysis_tools.py.md)
- [`iqra/modules/intelligence/anomaly_detector.py`](./iqra/modules/intelligence/anomaly_detector.py.md)
- [`iqra/modules/intelligence/auto_task_executor.py`](./iqra/modules/intelligence/auto_task_executor.py.md)
- [`iqra/modules/intelligence/batch_text.py`](./iqra/modules/intelligence/batch_text.py.md)
- [`iqra/modules/intelligence/business_ai_assistant.py`](./iqra/modules/intelligence/business_ai_assistant.py.md)
- [`iqra/modules/intelligence/business_tools.py`](./iqra/modules/intelligence/business_tools.py.md)
- [`iqra/modules/intelligence/chat_session_manager.py`](./iqra/modules/intelligence/chat_session_manager.py.md)
- [`iqra/modules/intelligence/compress_tool.py`](./iqra/modules/intelligence/compress_tool.py.md)
- [`iqra/modules/intelligence/core/__init__.py`](./iqra/modules/intelligence/core/__init__.py.md)
- [`iqra/modules/intelligence/core/llm_backend.py`](./iqra/modules/intelligence/core/llm_backend.py.md)
- [`iqra/modules/intelligence/crm_tools.py`](./iqra/modules/intelligence/crm_tools.py.md)
- [`iqra/modules/intelligence/data_import_tools.py`](./iqra/modules/intelligence/data_import_tools.py.md)
- [`iqra/modules/intelligence/data_visualization.py`](./iqra/modules/intelligence/data_visualization.py.md)
- [`iqra/modules/intelligence/db_helper.py`](./iqra/modules/intelligence/db_helper.py.md)
- [`iqra/modules/intelligence/download_dialog.py`](./iqra/modules/intelligence/download_dialog.py.md)
- [`iqra/modules/intelligence/editor_window.py`](./iqra/modules/intelligence/editor_window.py.md)
- [`iqra/modules/intelligence/enhanced/__init__.py`](./iqra/modules/intelligence/enhanced/__init__.py.md)
- [`iqra/modules/intelligence/enhanced/enhanced_tools.py`](./iqra/modules/intelligence/enhanced/enhanced_tools.py.md)
- [`iqra/modules/intelligence/enhanced_chat.py`](./iqra/modules/intelligence/enhanced_chat.py.md)
- [`iqra/modules/intelligence/event_trigger.py`](./iqra/modules/intelligence/event_trigger.py.md)
- [`iqra/modules/intelligence/file_rename_tools.py`](./iqra/modules/intelligence/file_rename_tools.py.md)
- [`iqra/modules/intelligence/finance_analysis_tools.py`](./iqra/modules/intelligence/finance_analysis_tools.py.md)
- [`iqra/modules/intelligence/floating_planet.py`](./iqra/modules/intelligence/floating_planet.py.md)
- [`iqra/modules/intelligence/floating_planet_anim_mixin.py`](./iqra/modules/intelligence/floating_planet_anim_mixin.py.md)
- [`iqra/modules/intelligence/floating_planet_draw_mixin.py`](./iqra/modules/intelligence/floating_planet_draw_mixin.py.md)
- [`iqra/modules/intelligence/floating_planet_menu_mixin.py`](./iqra/modules/intelligence/floating_planet_menu_mixin.py.md)
- [`iqra/modules/intelligence/hr_tools.py`](./iqra/modules/intelligence/hr_tools.py.md)
- [`iqra/modules/intelligence/img_converter.py`](./iqra/modules/intelligence/img_converter.py.md)
- [`iqra/modules/intelligence/intelligence_integration.py`](./iqra/modules/intelligence/intelligence_integration.py.md)
- [`iqra/modules/intelligence/intelligence_window.py`](./iqra/modules/intelligence/intelligence_window.py.md)
- [`iqra/modules/intelligence/inventory_tools.py`](./iqra/modules/intelligence/inventory_tools.py.md)
- [`iqra/modules/intelligence/iqra_floating_planet.py`](./iqra/modules/intelligence/iqra_floating_planet.py.md)
- [`iqra/modules/intelligence/json_tools.py`](./iqra/modules/intelligence/json_tools.py.md)
- [`iqra/modules/intelligence/key_manager.py`](./iqra/modules/intelligence/key_manager.py.md)
- [`iqra/modules/intelligence/knowledge_base.py`](./iqra/modules/intelligence/knowledge_base.py.md)
- [`iqra/modules/intelligence/marketing_tools.py`](./iqra/modules/intelligence/marketing_tools.py.md)
- [`iqra/modules/intelligence/model_config.py`](./iqra/modules/intelligence/model_config.py.md)
- [`iqra/modules/intelligence/monitor_dashboard.py`](./iqra/modules/intelligence/monitor_dashboard.py.md)
- [`iqra/modules/intelligence/offline_analyzer.py`](./iqra/modules/intelligence/offline_analyzer.py.md)
- [`iqra/modules/intelligence/password_tools.py`](./iqra/modules/intelligence/password_tools.py.md)
- [`iqra/modules/intelligence/performance_monitor.py`](./iqra/modules/intelligence/performance_monitor.py.md)
- [`iqra/modules/intelligence/predictor_window.py`](./iqra/modules/intelligence/predictor_window.py.md)
- [`iqra/modules/intelligence/quick_actions.py`](./iqra/modules/intelligence/quick_actions.py.md)
- [`iqra/modules/intelligence/quick_tools_panel.py`](./iqra/modules/intelligence/quick_tools_panel.py.md)
- [`iqra/modules/intelligence/rag_injector.py`](./iqra/modules/intelligence/rag_injector.py.md)
- [`iqra/modules/intelligence/recommendation_engine.py`](./iqra/modules/intelligence/recommendation_engine.py.md)
- [`iqra/modules/intelligence/report_generator.py`](./iqra/modules/intelligence/report_generator.py.md)
- [`iqra/modules/intelligence/sales_predictor.py`](./iqra/modules/intelligence/sales_predictor.py.md)
- [`iqra/modules/intelligence/scan_window.py`](./iqra/modules/intelligence/scan_window.py.md)
- [`iqra/modules/intelligence/screen_recorder.py`](./iqra/modules/intelligence/screen_recorder.py.md)
- [`iqra/modules/intelligence/self_monitor.py`](./iqra/modules/intelligence/self_monitor.py.md)
- [`iqra/modules/intelligence/session_context.py`](./iqra/modules/intelligence/session_context.py.md)
- [`iqra/modules/intelligence/smart_assistant.py`](./iqra/modules/intelligence/smart_assistant.py.md)
- [`iqra/modules/intelligence/smart_report_tools.py`](./iqra/modules/intelligence/smart_report_tools.py.md)
- [`iqra/modules/intelligence/smart_workflow.py`](./iqra/modules/intelligence/smart_workflow.py.md)
- [`iqra/modules/intelligence/solar_system_data.py`](./iqra/modules/intelligence/solar_system_data.py.md)
- [`iqra/modules/intelligence/solar_system_window.py`](./iqra/modules/intelligence/solar_system_window.py.md)
- [`iqra/modules/intelligence/super_intelligence.py`](./iqra/modules/intelligence/super_intelligence.py.md)
- [`iqra/modules/intelligence/system_hub_window.py`](./iqra/modules/intelligence/system_hub_window.py.md)
- [`iqra/modules/intelligence/system_monitor.py`](./iqra/modules/intelligence/system_monitor.py.md)
- [`iqra/modules/intelligence/text_editor.py`](./iqra/modules/intelligence/text_editor.py.md)
- [`iqra/modules/intelligence/timestamp_tools.py`](./iqra/modules/intelligence/timestamp_tools.py.md)
- [`iqra/modules/intelligence/tool_registry.py`](./iqra/modules/intelligence/tool_registry.py.md)
- [`iqra/modules/intelligence/tools_window.py`](./iqra/modules/intelligence/tools_window.py.md)
- [`iqra/modules/intelligence/usb_scanner.py`](./iqra/modules/intelligence/usb_scanner.py.md)
- [`iqra/modules/intelligence/vault_window.py`](./iqra/modules/intelligence/vault_window.py.md)
- [`iqra/modules/intelligence/voice_interface.py`](./iqra/modules/intelligence/voice_interface.py.md)
- [`iqra/modules/intelligence/whisper_recognizer.py`](./iqra/modules/intelligence/whisper_recognizer.py.md)
- [`iqra/modules/intelligence/window_top_tools.py`](./iqra/modules/intelligence/window_top_tools.py.md)
- [`iqra/modules/intelligence/workflow_engine.py`](./iqra/modules/intelligence/workflow_engine.py.md)
- [`iqra/planet_daemon.py`](./iqra/planet_daemon.py.md)
- [`iqra/rollback_control.py`](./iqra/rollback_control.py.md)
- [`iqra/services/__init__.py`](./iqra/services/__init__.py.md)
- [`iqra/services/ad_service.py`](./iqra/services/ad_service.py.md)
- [`iqra/services/ai_chatbot_service.py`](./iqra/services/ai_chatbot_service.py.md)
- [`iqra/services/audit_service.py`](./iqra/services/audit_service.py.md)
- [`iqra/services/backup_service.py`](./iqra/services/backup_service.py.md)
- [`iqra/services/backup_tool.py`](./iqra/services/backup_tool.py.md)
- [`iqra/services/barcode_service.py`](./iqra/services/barcode_service.py.md)
- [`iqra/services/bi_service.py`](./iqra/services/bi_service.py.md)
- [`iqra/services/cache_service.py`](./iqra/services/cache_service.py.md)
- [`iqra/services/chart_service.py`](./iqra/services/chart_service.py.md)
- [`iqra/services/database_optimizer.py`](./iqra/services/database_optimizer.py.md)
- [`iqra/services/encryption_service.py`](./iqra/services/encryption_service.py.md)
- [`iqra/services/export_service.py`](./iqra/services/export_service.py.md)
- [`iqra/services/hotkey_manager.py`](./iqra/services/hotkey_manager.py.md)
- [`iqra/services/i18n_service.py`](./iqra/services/i18n_service.py.md)
- [`iqra/services/image_cache_service.py`](./iqra/services/image_cache_service.py.md)
- [`iqra/services/import_export_service.py`](./iqra/services/import_export_service.py.md)
- [`iqra/services/lazy_load_service.py`](./iqra/services/lazy_load_service.py.md)
- [`iqra/services/license_service.py`](./iqra/services/license_service.py.md)
- [`iqra/services/logistics_service.py`](./iqra/services/logistics_service.py.md)
- [`iqra/services/memory_service.py`](./iqra/services/memory_service.py.md)
- [`iqra/services/nl_query_service.py`](./iqra/services/nl_query_service.py.md)
- [`iqra/services/notification_service.py`](./iqra/services/notification_service.py.md)
- [`iqra/services/offline_queue.py`](./iqra/services/offline_queue.py.md)
- [`iqra/services/payment_service.py`](./iqra/services/payment_service.py.md)
- [`iqra/services/performance_service.py`](./iqra/services/performance_service.py.md)
- [`iqra/services/permission_service.py`](./iqra/services/permission_service.py.md)
- [`iqra/services/print_service.py`](./iqra/services/print_service.py.md)
- [`iqra/services/realtime_service.py`](./iqra/services/realtime_service.py.md)
- [`iqra/services/sales_prediction_service.py`](./iqra/services/sales_prediction_service.py.md)
- [`iqra/services/scheduler_service.py`](./iqra/services/scheduler_service.py.md)
- [`iqra/services/sms_service.py`](./iqra/services/sms_service.py.md)
- [`iqra/services/sync_manager.py`](./iqra/services/sync_manager.py.md)
- [`iqra/services/system_service.py`](./iqra/services/system_service.py.md)
- [`iqra/services/system_tray.py`](./iqra/services/system_tray.py.md)
- [`iqra/services/template_service.py`](./iqra/services/template_service.py.md)
- [`iqra/services/theme_service.py`](./iqra/services/theme_service.py.md)
- [`iqra/services/update_service.py`](./iqra/services/update_service.py.md)
- [`iqra/services/workflow_service.py`](./iqra/services/workflow_service.py.md)
- [`iqra/siri_command_handler.py`](./iqra/siri_command_handler.py.md)
- [`iqra/solar_explorer/__init__.py`](./iqra/solar_explorer/__init__.py.md)
- [`iqra/solar_explorer/_dwarf_planets.py`](./iqra/solar_explorer/_dwarf_planets.py.md)
- [`iqra/solar_explorer/_moons.py`](./iqra/solar_explorer/_moons.py.md)
- [`iqra/solar_explorer/_planets.py`](./iqra/solar_explorer/_planets.py.md)
- [`iqra/solar_explorer/_sun.py`](./iqra/solar_explorer/_sun.py.md)
- [`iqra/solar_explorer/body_data_entries.py`](./iqra/solar_explorer/body_data_entries.py.md)
- [`iqra/solar_explorer/body_detail_window.py`](./iqra/solar_explorer/body_detail_window.py.md)
- [`iqra/solar_explorer/body_encyclopedia.py`](./iqra/solar_explorer/body_encyclopedia.py.md)
- [`iqra/solar_explorer/star_catalog_window.py`](./iqra/solar_explorer/star_catalog_window.py.md)
- [`iqra/solar_explorer/voice_reader.py`](./iqra/solar_explorer/voice_reader.py.md)
- [`iqra/tools/__init__.py`](./iqra/tools/__init__.py.md)
- [`iqra/tools/check_imports.py`](./iqra/tools/check_imports.py.md)
- [`iqra/tools/environments/__init__.py`](./iqra/tools/environments/__init__.py.md)
- [`iqra/tools/environments/file_sync.py`](./iqra/tools/environments/file_sync.py.md)
- [`iqra/tools/module_health.py`](./iqra/tools/module_health.py.md)
- [`iqra/tools/skills_sync.py`](./iqra/tools/skills_sync.py.md)
- [`iqra/utils.py`](./iqra/utils.py.md)
- [`management-system/_archived/dedup_20260619_170800/deps.py`](./management-system/_archived/dedup_20260619_170800/deps.py.md)
- [`management-system/_archived/license_模块归档_20260619/license_crypto.py`](./management-system/_archived/license_模块归档_20260619/license_crypto.py.md)
- [`management-system/_archived/license_模块归档_20260619/license_db.py`](./management-system/_archived/license_模块归档_20260619/license_db.py.md)
- [`management-system/_archived/license_模块归档_20260619/license_service.py`](./management-system/_archived/license_模块归档_20260619/license_service.py.md)
- [`management-system/config/__init__.py`](./management-system/config/__init__.py.md)
- [`management-system/config/supabase_config.py`](./management-system/config/supabase_config.py.md)
- [`management-system/core/__init__.py`](./management-system/core/__init__.py.md)
- [`management-system/core/_deprecated/cloud_sync_v2.py`](./management-system/core/_deprecated/cloud_sync_v2.py.md)
- [`management-system/core/_deprecated/sync_optimized.py`](./management-system/core/_deprecated/sync_optimized.py.md)
- [`management-system/core/_deprecated/triple_sync.py`](./management-system/core/_deprecated/triple_sync.py.md)
- [`management-system/core/agent.py`](./management-system/core/agent.py.md)
- [`management-system/core/app_state.py`](./management-system/core/app_state.py.md)
- [`management-system/core/auth_service.py`](./management-system/core/auth_service.py.md)
- [`management-system/core/backup.py`](./management-system/core/backup.py.md)
- [`management-system/core/business_service.py`](./management-system/core/business_service.py.md)
- [`management-system/core/ceo_agent.py`](./management-system/core/ceo_agent.py.md)
- [`management-system/core/cloud_pull.py`](./management-system/core/cloud_pull.py.md)
- [`management-system/core/cloud_sync.py`](./management-system/core/cloud_sync.py.md)
- [`management-system/core/conflict_resolver.py`](./management-system/core/conflict_resolver.py.md)
- [`management-system/core/cosmic.py`](./management-system/core/cosmic.py.md)
- [`management-system/core/custom_fields.py`](./management-system/core/custom_fields.py.md)
- [`management-system/core/dark_theme.py`](./management-system/core/dark_theme.py.md)
- [`management-system/core/dark_tool_theme.py`](./management-system/core/dark_tool_theme.py.md)
- [`management-system/core/data.py`](./management-system/core/data.py.md)
- [`management-system/core/data_sync.py`](./management-system/core/data_sync.py.md)
- [`management-system/core/database.py`](./management-system/core/database.py.md)
- [`management-system/core/event_bus.py`](./management-system/core/event_bus.py.md)
- [`management-system/core/excel_export.py`](./management-system/core/excel_export.py.md)
- [`management-system/core/llm_client.py`](./management-system/core/llm_client.py.md)
- [`management-system/core/machine_code.py`](./management-system/core/machine_code.py.md)
- [`management-system/core/mobile_api.py`](./management-system/core/mobile_api.py.md)
- [`management-system/core/module_manager.py`](./management-system/core/module_manager.py.md)
- [`management-system/core/modules/__init__.py`](./management-system/core/modules/__init__.py.md)
- [`management-system/core/modules/supabase/__init__.py`](./management-system/core/modules/supabase/__init__.py.md)
- [`management-system/core/modules/supabase/_core.py`](./management-system/core/modules/supabase/_core.py.md)
- [`management-system/core/modules/supabase/activation.py`](./management-system/core/modules/supabase/activation.py.md)
- [`management-system/core/modules/supabase/admin_log.py`](./management-system/core/modules/supabase/admin_log.py.md)
- [`management-system/core/modules/supabase/auth.py`](./management-system/core/modules/supabase/auth.py.md)
- [`management-system/core/modules/supabase/business.py`](./management-system/core/modules/supabase/business.py.md)
- [`management-system/core/modules/supabase/distribution.py`](./management-system/core/modules/supabase/distribution.py.md)
- [`management-system/core/modules/supabase/member.py`](./management-system/core/modules/supabase/member.py.md)
- [`management-system/core/modules/supabase/updater.py`](./management-system/core/modules/supabase/updater.py.md)
- [`management-system/core/modules/supabase/wallet.py`](./management-system/core/modules/supabase/wallet.py.md)
- [`management-system/core/notification_cron.py`](./management-system/core/notification_cron.py.md)
- [`management-system/core/notification_service.py`](./management-system/core/notification_service.py.md)
- [`management-system/core/notification_toast.py`](./management-system/core/notification_toast.py.md)
- [`management-system/core/operation_log.py`](./management-system/core/operation_log.py.md)
- [`management-system/core/oplog.py`](./management-system/core/oplog.py.md)
- [`management-system/core/paths.py`](./management-system/core/paths.py.md)
- [`management-system/core/planet_painter.py`](./management-system/core/planet_painter.py.md)
- [`management-system/core/procedural_texture.py`](./management-system/core/procedural_texture.py.md)
- [`management-system/core/reconciliation.py`](./management-system/core/reconciliation.py.md)
- [`management-system/core/scheduled_tasks.py`](./management-system/core/scheduled_tasks.py.md)
- [`management-system/core/shapes/__init__.py`](./management-system/core/shapes/__init__.py.md)
- [`management-system/core/shapes/alien.py`](./management-system/core/shapes/alien.py.md)
- [`management-system/core/shapes/black_hole.py`](./management-system/core/shapes/black_hole.py.md)
- [`management-system/core/shapes/classic.py`](./management-system/core/shapes/classic.py.md)
- [`management-system/core/shapes/comet.py`](./management-system/core/shapes/comet.py.md)
- [`management-system/core/shapes/corvette.py`](./management-system/core/shapes/corvette.py.md)
- [`management-system/core/shapes/crystal_alien.py`](./management-system/core/shapes/crystal_alien.py.md)
- [`management-system/core/shapes/destroyer.py`](./management-system/core/shapes/destroyer.py.md)
- [`management-system/core/shapes/dreadnought.py`](./management-system/core/shapes/dreadnought.py.md)
- [`management-system/core/shapes/energy_being.py`](./management-system/core/shapes/energy_being.py.md)
- [`management-system/core/shapes/fighter.py`](./management-system/core/shapes/fighter.py.md)
- [`management-system/core/shapes/gas_giant.py`](./management-system/core/shapes/gas_giant.py.md)
- [`management-system/core/shapes/ghost_alien.py`](./management-system/core/shapes/ghost_alien.py.md)
- [`management-system/core/shapes/grey_alien.py`](./management-system/core/shapes/grey_alien.py.md)
- [`management-system/core/shapes/ice_giant.py`](./management-system/core/shapes/ice_giant.py.md)
- [`management-system/core/shapes/interceptor.py`](./management-system/core/shapes/interceptor.py.md)
- [`management-system/core/shapes/jellyfish_alien.py`](./management-system/core/shapes/jellyfish_alien.py.md)
- [`management-system/core/shapes/lava_planet.py`](./management-system/core/shapes/lava_planet.py.md)
- [`management-system/core/shapes/mars.py`](./management-system/core/shapes/mars.py.md)
- [`management-system/core/shapes/mercury.py`](./management-system/core/shapes/mercury.py.md)
- [`management-system/core/shapes/nebula.py`](./management-system/core/shapes/nebula.py.md)
- [`management-system/core/shapes/neutron_star.py`](./management-system/core/shapes/neutron_star.py.md)
- [`management-system/core/shapes/octopus_alien.py`](./management-system/core/shapes/octopus_alien.py.md)
- [`management-system/core/shapes/pluto.py`](./management-system/core/shapes/pluto.py.md)
- [`management-system/core/shapes/pulsar.py`](./management-system/core/shapes/pulsar.py.md)
- [`management-system/core/shapes/red_giant.py`](./management-system/core/shapes/red_giant.py.md)
- [`management-system/core/shapes/reptilian.py`](./management-system/core/shapes/reptilian.py.md)
- [`management-system/core/shapes/robot_alien.py`](./management-system/core/shapes/robot_alien.py.md)
- [`management-system/core/shapes/saturn.py`](./management-system/core/shapes/saturn.py.md)
- [`management-system/core/shapes/scout.py`](./management-system/core/shapes/scout.py.md)
- [`management-system/core/shapes/starship.py`](./management-system/core/shapes/starship.py.md)
- [`management-system/core/shapes/transporter.py`](./management-system/core/shapes/transporter.py.md)
- [`management-system/core/shapes/uranus.py`](./management-system/core/shapes/uranus.py.md)
- [`management-system/core/shapes/venus.py`](./management-system/core/shapes/venus.py.md)
- [`management-system/core/shapes/white_dwarf.py`](./management-system/core/shapes/white_dwarf.py.md)
- [`management-system/core/shapes/wormhole.py`](./management-system/core/shapes/wormhole.py.md)
- [`management-system/core/simple_sync.py`](./management-system/core/simple_sync.py.md)
- [`management-system/core/smart_report.py`](./management-system/core/smart_report.py.md)
- [`management-system/core/storage.py`](./management-system/core/storage.py.md)
- [`management-system/core/supabase_client.py`](./management-system/core/supabase_client.py.md)
- [`management-system/core/sync_bridge.py`](./management-system/core/sync_bridge.py.md)
- [`management-system/core/sync_decorator.py`](./management-system/core/sync_decorator.py.md)
- [`management-system/core/sync_integration.py`](./management-system/core/sync_integration.py.md)
- [`management-system/core/sync_manager.py`](./management-system/core/sync_manager.py.md)
- [`management-system/core/texture_mapper.py`](./management-system/core/texture_mapper.py.md)
- [`management-system/core/theme.py`](./management-system/core/theme.py.md)
- [`management-system/core/user_dao.py`](./management-system/core/user_dao.py.md)
- [`management-system/core/voice.py`](./management-system/core/voice.py.md)
- [`management-system/core/workflow_engine.py`](./management-system/core/workflow_engine.py.md)
- [`management-system/modules/__init__.py`](./management-system/modules/__init__.py.md)
- [`management-system/modules/admin/__init__.py`](./management-system/modules/admin/__init__.py.md)
- [`management-system/modules/admin/admin_activation.py`](./management-system/modules/admin/admin_activation.py.md)
- [`management-system/modules/admin/admin_backup.py`](./management-system/modules/admin/admin_backup.py.md)
- [`management-system/modules/admin/admin_data.py`](./management-system/modules/admin/admin_data.py.md)
- [`management-system/modules/admin/admin_data_mgmt.py`](./management-system/modules/admin/admin_data_mgmt.py.md)
- [`management-system/modules/admin/admin_finance.py`](./management-system/modules/admin/admin_finance.py.md)
- [`management-system/modules/admin/admin_log.py`](./management-system/modules/admin/admin_log.py.md)
- [`management-system/modules/admin/admin_orders.py`](./management-system/modules/admin/admin_orders.py.md)
- [`management-system/modules/admin/admin_product.py`](./management-system/modules/admin/admin_product.py.md)
- [`management-system/modules/admin/admin_service.py`](./management-system/modules/admin/admin_service.py.md)
- [`management-system/modules/admin/admin_settings.py`](./management-system/modules/admin/admin_settings.py.md)
- [`management-system/modules/admin/admin_staff.py`](./management-system/modules/admin/admin_staff.py.md)
- [`management-system/modules/admin/admin_strategy.py`](./management-system/modules/admin/admin_strategy.py.md)
- [`management-system/modules/admin/admin_user.py`](./management-system/modules/admin/admin_user.py.md)
- [`management-system/modules/admin/admin_window.py`](./management-system/modules/admin/admin_window.py.md)
- [`management-system/modules/admin/cascade_delete.py`](./management-system/modules/admin/cascade_delete.py.md)
- [`management-system/modules/admin/strategy_dao.py`](./management-system/modules/admin/strategy_dao.py.md)
- [`management-system/modules/auth/__init__.py`](./management-system/modules/auth/__init__.py.md)
- [`management-system/modules/auth/upgrade_window.py`](./management-system/modules/auth/upgrade_window.py.md)
- [`management-system/modules/system/__init__.py`](./management-system/modules/system/__init__.py.md)
- [`management-system/modules/system/cloud_model_panel.py`](./management-system/modules/system/cloud_model_panel.py.md)
- [`management-system/modules/system/cloud_module.py`](./management-system/modules/system/cloud_module.py.md)
- [`management-system/modules/system/cloud_server_window.py`](./management-system/modules/system/cloud_server_window.py.md)
- [`management-system/modules/system/cloud_window.py`](./management-system/modules/system/cloud_window.py.md)
- [`management-system/rollback_control.py`](./management-system/rollback_control.py.md)
- [`management-system/services/__init__.py`](./management-system/services/__init__.py.md)
- [`management-system/services/ai_chatbot_service.py`](./management-system/services/ai_chatbot_service.py.md)
- [`management-system/services/audit_service.py`](./management-system/services/audit_service.py.md)
- [`management-system/services/backup_service.py`](./management-system/services/backup_service.py.md)
- [`management-system/services/backup_tool.py`](./management-system/services/backup_tool.py.md)
- [`management-system/services/barcode_service.py`](./management-system/services/barcode_service.py.md)
- [`management-system/services/bi_service.py`](./management-system/services/bi_service.py.md)
- [`management-system/services/cache_service.py`](./management-system/services/cache_service.py.md)
- [`management-system/services/chart_service.py`](./management-system/services/chart_service.py.md)
- [`management-system/services/database_optimizer.py`](./management-system/services/database_optimizer.py.md)
- [`management-system/services/encryption_service.py`](./management-system/services/encryption_service.py.md)
- [`management-system/services/export_service.py`](./management-system/services/export_service.py.md)
- [`management-system/services/i18n_service.py`](./management-system/services/i18n_service.py.md)
- [`management-system/services/image_cache_service.py`](./management-system/services/image_cache_service.py.md)
- [`management-system/services/import_export_service.py`](./management-system/services/import_export_service.py.md)
- [`management-system/services/lazy_load_service.py`](./management-system/services/lazy_load_service.py.md)
- [`management-system/services/license_service.py`](./management-system/services/license_service.py.md)
- [`management-system/services/logistics_service.py`](./management-system/services/logistics_service.py.md)
- [`management-system/services/memory_service.py`](./management-system/services/memory_service.py.md)
- [`management-system/services/nl_query_service.py`](./management-system/services/nl_query_service.py.md)
- [`management-system/services/notification_service.py`](./management-system/services/notification_service.py.md)
- [`management-system/services/offline_queue.py`](./management-system/services/offline_queue.py.md)
- [`management-system/services/payment_service.py`](./management-system/services/payment_service.py.md)
- [`management-system/services/performance_service.py`](./management-system/services/performance_service.py.md)
- [`management-system/services/permission_service.py`](./management-system/services/permission_service.py.md)
- [`management-system/services/print_service.py`](./management-system/services/print_service.py.md)
- [`management-system/services/realtime_service.py`](./management-system/services/realtime_service.py.md)
- [`management-system/services/sales_prediction_service.py`](./management-system/services/sales_prediction_service.py.md)
- [`management-system/services/scheduler_service.py`](./management-system/services/scheduler_service.py.md)
- [`management-system/services/sms_service.py`](./management-system/services/sms_service.py.md)
- [`management-system/services/sync_manager.py`](./management-system/services/sync_manager.py.md)
- [`management-system/services/system_service.py`](./management-system/services/system_service.py.md)
- [`management-system/services/system_tray.py`](./management-system/services/system_tray.py.md)
- [`management-system/services/template_service.py`](./management-system/services/template_service.py.md)
- [`management-system/services/theme_service.py`](./management-system/services/theme_service.py.md)
- [`management-system/services/update_service.py`](./management-system/services/update_service.py.md)
- [`management-system/services/workflow_service.py`](./management-system/services/workflow_service.py.md)
- [`management-system/siri_command_handler.py`](./management-system/siri_command_handler.py.md)
- [`management-system/tools/__init__.py`](./management-system/tools/__init__.py.md)
- [`management-system/tools/environments/__init__.py`](./management-system/tools/environments/__init__.py.md)
- [`modules/__init__.py`](./modules/__init__.py.md)
- [`modules/admin/__init__.py`](./modules/admin/__init__.py.md)
- [`modules/admin/admin_activation.py`](./modules/admin/admin_activation.py.md)
- [`modules/admin/admin_backup.py`](./modules/admin/admin_backup.py.md)
- [`modules/admin/admin_data.py`](./modules/admin/admin_data.py.md)
- [`modules/admin/admin_data_mgmt.py`](./modules/admin/admin_data_mgmt.py.md)
- [`modules/admin/admin_finance.py`](./modules/admin/admin_finance.py.md)
- [`modules/admin/admin_log.py`](./modules/admin/admin_log.py.md)
- [`modules/admin/admin_orders.py`](./modules/admin/admin_orders.py.md)
- [`modules/admin/admin_product.py`](./modules/admin/admin_product.py.md)
- [`modules/admin/admin_service.py`](./modules/admin/admin_service.py.md)
- [`modules/admin/admin_settings.py`](./modules/admin/admin_settings.py.md)
- [`modules/admin/admin_staff.py`](./modules/admin/admin_staff.py.md)
- [`modules/admin/admin_strategy.py`](./modules/admin/admin_strategy.py.md)
- [`modules/admin/admin_user.py`](./modules/admin/admin_user.py.md)
- [`modules/admin/admin_window.py`](./modules/admin/admin_window.py.md)
- [`modules/admin/cascade_delete.py`](./modules/admin/cascade_delete.py.md)
- [`modules/admin/strategy_dao.py`](./modules/admin/strategy_dao.py.md)
- [`modules/astronomy/__init__.py`](./modules/astronomy/__init__.py.md)
- [`modules/astronomy/hub.py`](./modules/astronomy/hub.py.md)
- [`modules/astronomy/solar_system/__init__.py`](./modules/astronomy/solar_system/__init__.py.md)
- [`modules/astronomy/solar_system/data.py`](./modules/astronomy/solar_system/data.py.md)
- [`modules/astronomy/solar_system/planets/__init__.py`](./modules/astronomy/solar_system/planets/__init__.py.md)
- [`modules/astronomy/solar_system/planets/_base.py`](./modules/astronomy/solar_system/planets/_base.py.md)
- [`modules/astronomy/solar_system/planets/callisto/__init__.py`](./modules/astronomy/solar_system/planets/callisto/__init__.py.md)
- [`modules/astronomy/solar_system/planets/ceres/__init__.py`](./modules/astronomy/solar_system/planets/ceres/__init__.py.md)
- [`modules/astronomy/solar_system/planets/earth/__init__.py`](./modules/astronomy/solar_system/planets/earth/__init__.py.md)
- [`modules/astronomy/solar_system/planets/enceladus/__init__.py`](./modules/astronomy/solar_system/planets/enceladus/__init__.py.md)
- [`modules/astronomy/solar_system/planets/eris/__init__.py`](./modules/astronomy/solar_system/planets/eris/__init__.py.md)
- [`modules/astronomy/solar_system/planets/europa/__init__.py`](./modules/astronomy/solar_system/planets/europa/__init__.py.md)
- [`modules/astronomy/solar_system/planets/ganymede/__init__.py`](./modules/astronomy/solar_system/planets/ganymede/__init__.py.md)
- [`modules/astronomy/solar_system/planets/haumea/__init__.py`](./modules/astronomy/solar_system/planets/haumea/__init__.py.md)
- [`modules/astronomy/solar_system/planets/io/__init__.py`](./modules/astronomy/solar_system/planets/io/__init__.py.md)
- [`modules/astronomy/solar_system/planets/jupiter/__init__.py`](./modules/astronomy/solar_system/planets/jupiter/__init__.py.md)
- [`modules/astronomy/solar_system/planets/makemake/__init__.py`](./modules/astronomy/solar_system/planets/makemake/__init__.py.md)
- [`modules/astronomy/solar_system/planets/mars/__init__.py`](./modules/astronomy/solar_system/planets/mars/__init__.py.md)
- [`modules/astronomy/solar_system/planets/mercury/__init__.py`](./modules/astronomy/solar_system/planets/mercury/__init__.py.md)
- [`modules/astronomy/solar_system/planets/moon/__init__.py`](./modules/astronomy/solar_system/planets/moon/__init__.py.md)
- [`modules/astronomy/solar_system/planets/neptune/__init__.py`](./modules/astronomy/solar_system/planets/neptune/__init__.py.md)
- [`modules/astronomy/solar_system/planets/pluto/__init__.py`](./modules/astronomy/solar_system/planets/pluto/__init__.py.md)
- [`modules/astronomy/solar_system/planets/saturn/__init__.py`](./modules/astronomy/solar_system/planets/saturn/__init__.py.md)
- [`modules/astronomy/solar_system/planets/sun/__init__.py`](./modules/astronomy/solar_system/planets/sun/__init__.py.md)
- [`modules/astronomy/solar_system/planets/titan/__init__.py`](./modules/astronomy/solar_system/planets/titan/__init__.py.md)
- [`modules/astronomy/solar_system/planets/uranus/__init__.py`](./modules/astronomy/solar_system/planets/uranus/__init__.py.md)
- [`modules/astronomy/solar_system/planets/venus/__init__.py`](./modules/astronomy/solar_system/planets/venus/__init__.py.md)
- [`modules/astronomy/solar_system/renderer.py`](./modules/astronomy/solar_system/renderer.py.md)
- [`modules/astronomy/solar_system/window.py`](./modules/astronomy/solar_system/window.py.md)
- [`modules/astronomy/star_catalog/__init__.py`](./modules/astronomy/star_catalog/__init__.py.md)
- [`modules/astronomy/star_catalog/catalog.py`](./modules/astronomy/star_catalog/catalog.py.md)
- [`modules/astronomy/star_catalog/data_entries.py`](./modules/astronomy/star_catalog/data_entries.py.md)
- [`modules/astronomy/star_catalog/detail.py`](./modules/astronomy/star_catalog/detail.py.md)
- [`modules/astronomy/star_catalog/encyclopedia.py`](./modules/astronomy/star_catalog/encyclopedia.py.md)
- [`modules/astronomy/star_catalog/voice.py`](./modules/astronomy/star_catalog/voice.py.md)
- [`modules/auth/__init__.py`](./modules/auth/__init__.py.md)
- [`modules/auth/auth_service.py`](./modules/auth/auth_service.py.md)
- [`modules/auth/auth_service_membership.py`](./modules/auth/auth_service_membership.py.md)
- [`modules/auth/auth_service_sync.py`](./modules/auth/auth_service_sync.py.md)
- [`modules/auth/dao/__init__.py`](./modules/auth/dao/__init__.py.md)
- [`modules/auth/dao/session_dao.py`](./modules/auth/dao/session_dao.py.md)
- [`modules/auth/dao/user_dao.py`](./modules/auth/dao/user_dao.py.md)
- [`modules/auth/login_window.py`](./modules/auth/login_window.py.md)
- [`modules/auth/model_setup_window.py`](./modules/auth/model_setup_window.py.md)
- [`modules/intelligence/__init__.py`](./modules/intelligence/__init__.py.md)
- [`modules/intelligence/solar_system_data.py`](./modules/intelligence/solar_system_data.py.md)
- [`modules/supabase/__init__.py`](./modules/supabase/__init__.py.md)
- [`modules/supabase/auth.py`](./modules/supabase/auth.py.md)
- [`modules/system/__init__.py`](./modules/system/__init__.py.md)
- [`modules/system/_archived/activation_window.py`](./modules/system/_archived/activation_window.py.md)
- [`modules/system/_archived/base_info_window.py`](./modules/system/_archived/base_info_window.py.md)
- [`modules/system/_archived/cloud_window.py`](./modules/system/_archived/cloud_window.py.md)
- [`modules/system/_archived/logs_window.py`](./modules/system/_archived/logs_window.py.md)
- [`modules/system/_archived/system_window.py`](./modules/system/_archived/system_window.py.md)
- [`modules/system/_archived/update_dialog.py`](./modules/system/_archived/update_dialog.py.md)
- [`modules/system/astronomy_hub_window.py`](./modules/system/astronomy_hub_window.py.md)
- [`modules/system/audit_window.py`](./modules/system/audit_window.py.md)
- [`modules/system/base_info_window.py`](./modules/system/base_info_window.py.md)
- [`modules/system/cloud_model_panel.py`](./modules/system/cloud_model_panel.py.md)
- [`modules/system/cloud_module.py`](./modules/system/cloud_module.py.md)
- [`modules/system/cloud_server_window.py`](./modules/system/cloud_server_window.py.md)
- [`modules/system/cloud_window.py`](./modules/system/cloud_window.py.md)
- [`modules/system/logs_window.py`](./modules/system/logs_window.py.md)
- [`modules/system/system_hub_window.py`](./modules/system/system_hub_window.py.md)
- [`modules/system/system_logs_service.py`](./modules/system/system_logs_service.py.md)
- [`planetarium/config/__init__.py`](./planetarium/config/__init__.py.md)
- [`planetarium/config/supabase_config.py`](./planetarium/config/supabase_config.py.md)
- [`planetarium/core/__init__.py`](./planetarium/core/__init__.py.md)
- [`planetarium/core/_deprecated/cloud_sync_v2.py`](./planetarium/core/_deprecated/cloud_sync_v2.py.md)
- [`planetarium/core/_deprecated/sync_optimized.py`](./planetarium/core/_deprecated/sync_optimized.py.md)
- [`planetarium/core/_deprecated/triple_sync.py`](./planetarium/core/_deprecated/triple_sync.py.md)
- [`planetarium/core/agent.py`](./planetarium/core/agent.py.md)
- [`planetarium/core/app_state.py`](./planetarium/core/app_state.py.md)
- [`planetarium/core/auth_service.py`](./planetarium/core/auth_service.py.md)
- [`planetarium/core/backup.py`](./planetarium/core/backup.py.md)
- [`planetarium/core/cloud_pull.py`](./planetarium/core/cloud_pull.py.md)
- [`planetarium/core/cloud_sync.py`](./planetarium/core/cloud_sync.py.md)
- [`planetarium/core/conflict_resolver.py`](./planetarium/core/conflict_resolver.py.md)
- [`planetarium/core/cosmic.py`](./planetarium/core/cosmic.py.md)
- [`planetarium/core/dark_theme.py`](./planetarium/core/dark_theme.py.md)
- [`planetarium/core/dark_tool_theme.py`](./planetarium/core/dark_tool_theme.py.md)
- [`planetarium/core/data.py`](./planetarium/core/data.py.md)
- [`planetarium/core/data_sync.py`](./planetarium/core/data_sync.py.md)
- [`planetarium/core/database.py`](./planetarium/core/database.py.md)
- [`planetarium/core/event_bus.py`](./planetarium/core/event_bus.py.md)
- [`planetarium/core/llm_client.py`](./planetarium/core/llm_client.py.md)
- [`planetarium/core/machine_code.py`](./planetarium/core/machine_code.py.md)
- [`planetarium/core/module_manager.py`](./planetarium/core/module_manager.py.md)
- [`planetarium/core/modules/__init__.py`](./planetarium/core/modules/__init__.py.md)
- [`planetarium/core/modules/intelligence/__init__.py`](./planetarium/core/modules/intelligence/__init__.py.md)
- [`planetarium/core/modules/intelligence/_ai_shared.py`](./planetarium/core/modules/intelligence/_ai_shared.py.md)
- [`planetarium/core/modules/intelligence/_chat_dialog/__init__.py`](./planetarium/core/modules/intelligence/_chat_dialog/__init__.py.md)
- [`planetarium/core/modules/intelligence/_chat_dialog/_dialog.py`](./planetarium/core/modules/intelligence/_chat_dialog/_dialog.py.md)
- [`planetarium/core/modules/intelligence/_chat_dialog.py`](./planetarium/core/modules/intelligence/_chat_dialog.py.md)
- [`planetarium/core/modules/intelligence/_compat.py`](./planetarium/core/modules/intelligence/_compat.py.md)
- [`planetarium/core/modules/intelligence/_model_manager_download.py`](./planetarium/core/modules/intelligence/_model_manager_download.py.md)
- [`planetarium/core/modules/intelligence/_model_manager_ollama.py`](./planetarium/core/modules/intelligence/_model_manager_ollama.py.md)
- [`planetarium/core/modules/intelligence/_stubs.py`](./planetarium/core/modules/intelligence/_stubs.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/__init__.py`](./planetarium/core/modules/intelligence/agent_bridge/__init__.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/_core.py`](./planetarium/core/modules/intelligence/agent_bridge/_core.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/_engine_mixin.py`](./planetarium/core/modules/intelligence/agent_bridge/_engine_mixin.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_models.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_models.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/__init__.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/__init__.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_code_tools.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_code_tools.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_file_tools.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_file_tools.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_system_tools.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_system_tools.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_task_tools.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_task_tools.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_web_tools.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_web_tools.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_workers.py`](./planetarium/core/modules/intelligence/agent_bridge/agent_bridge_workers.py.md)
- [`planetarium/core/modules/intelligence/agent_bridge.py`](./planetarium/core/modules/intelligence/agent_bridge.py.md)
- [`planetarium/core/modules/intelligence/enhanced/__init__.py`](./planetarium/core/modules/intelligence/enhanced/__init__.py.md)
- [`planetarium/core/modules/intelligence/enhanced/_enhanced_base.py`](./planetarium/core/modules/intelligence/enhanced/_enhanced_base.py.md)
- [`planetarium/core/modules/intelligence/enhanced/_enhanced_files_mixin.py`](./planetarium/core/modules/intelligence/enhanced/_enhanced_files_mixin.py.md)
- [`planetarium/core/modules/intelligence/enhanced/_enhanced_storage_mixin.py`](./planetarium/core/modules/intelligence/enhanced/_enhanced_storage_mixin.py.md)
- [`planetarium/core/modules/intelligence/enhanced/_enhanced_system_mixin.py`](./planetarium/core/modules/intelligence/enhanced/_enhanced_system_mixin.py.md)
- [`planetarium/core/modules/intelligence/enhanced/_enhanced_web_mixin.py`](./planetarium/core/modules/intelligence/enhanced/_enhanced_web_mixin.py.md)
- [`planetarium/core/modules/intelligence/enhanced/enhanced_tools.py`](./planetarium/core/modules/intelligence/enhanced/enhanced_tools.py.md)
- [`planetarium/core/modules/intelligence/intelligence_integration.py`](./planetarium/core/modules/intelligence/intelligence_integration.py.md)
- [`planetarium/core/modules/intelligence/marketing_tools/__init__.py`](./planetarium/core/modules/intelligence/marketing_tools/__init__.py.md)
- [`planetarium/core/modules/intelligence/marketing_tools/_core.py`](./planetarium/core/modules/intelligence/marketing_tools/_core.py.md)
- [`planetarium/core/modules/intelligence/marketing_tools/_registration.py`](./planetarium/core/modules/intelligence/marketing_tools/_registration.py.md)
- [`planetarium/core/modules/intelligence/marketing_tools.py`](./planetarium/core/modules/intelligence/marketing_tools.py.md)
- [`planetarium/core/modules/intelligence/quick_tools_panel/__init__.py`](./planetarium/core/modules/intelligence/quick_tools_panel/__init__.py.md)
- [`planetarium/core/modules/intelligence/quick_tools_panel/_api_config.py`](./planetarium/core/modules/intelligence/quick_tools_panel/_api_config.py.md)
- [`planetarium/core/modules/intelligence/quick_tools_panel/_quick_tools.py`](./planetarium/core/modules/intelligence/quick_tools_panel/_quick_tools.py.md)
- [`planetarium/core/modules/intelligence/quick_tools_panel.py`](./planetarium/core/modules/intelligence/quick_tools_panel.py.md)
- [`planetarium/core/modules/intelligence/session_context.py`](./planetarium/core/modules/intelligence/session_context.py.md)
- [`planetarium/core/modules/intelligence/solar_system_data/__init__.py`](./planetarium/core/modules/intelligence/solar_system_data/__init__.py.md)
- [`planetarium/core/modules/intelligence/solar_system_data/_catalog.py`](./planetarium/core/modules/intelligence/solar_system_data/_catalog.py.md)
- [`planetarium/core/modules/intelligence/solar_system_data/_core.py`](./planetarium/core/modules/intelligence/solar_system_data/_core.py.md)
- [`planetarium/core/modules/intelligence/solar_system_data/_data.py`](./planetarium/core/modules/intelligence/solar_system_data/_data.py.md)
- [`planetarium/core/modules/intelligence/solar_system_data.py`](./planetarium/core/modules/intelligence/solar_system_data.py.md)
- [`planetarium/core/modules/intelligence/super_intelligence.py`](./planetarium/core/modules/intelligence/super_intelligence.py.md)
- [`planetarium/core/modules/intelligence/text_editor/__init__.py`](./planetarium/core/modules/intelligence/text_editor/__init__.py.md)
- [`planetarium/core/modules/intelligence/text_editor/_core.py`](./planetarium/core/modules/intelligence/text_editor/_core.py.md)
- [`planetarium/core/modules/intelligence/text_editor/_crypto.py`](./planetarium/core/modules/intelligence/text_editor/_crypto.py.md)
- [`planetarium/core/modules/intelligence/text_editor/_note_tab.py`](./planetarium/core/modules/intelligence/text_editor/_note_tab.py.md)
- [`planetarium/core/modules/intelligence/text_editor.py`](./planetarium/core/modules/intelligence/text_editor.py.md)
- [`planetarium/core/modules/intelligence/tool_registry.py`](./planetarium/core/modules/intelligence/tool_registry.py.md)
- [`planetarium/core/modules/intelligence/workflow_engine/__init__.py`](./planetarium/core/modules/intelligence/workflow_engine/__init__.py.md)
- [`planetarium/core/modules/intelligence/workflow_engine/_engine.py`](./planetarium/core/modules/intelligence/workflow_engine/_engine.py.md)
- [`planetarium/core/modules/intelligence/workflow_engine/_models.py`](./planetarium/core/modules/intelligence/workflow_engine/_models.py.md)
- [`planetarium/core/modules/intelligence/workflow_engine.py`](./planetarium/core/modules/intelligence/workflow_engine.py.md)
- [`planetarium/core/modules/supabase/__init__.py`](./planetarium/core/modules/supabase/__init__.py.md)
- [`planetarium/core/modules/supabase/_core.py`](./planetarium/core/modules/supabase/_core.py.md)
- [`planetarium/core/modules/supabase/activation.py`](./planetarium/core/modules/supabase/activation.py.md)
- [`planetarium/core/modules/supabase/admin_log.py`](./planetarium/core/modules/supabase/admin_log.py.md)
- [`planetarium/core/modules/supabase/auth.py`](./planetarium/core/modules/supabase/auth.py.md)
- [`planetarium/core/modules/supabase/business.py`](./planetarium/core/modules/supabase/business.py.md)
- [`planetarium/core/modules/supabase/distribution.py`](./planetarium/core/modules/supabase/distribution.py.md)
- [`planetarium/core/modules/supabase/member.py`](./planetarium/core/modules/supabase/member.py.md)
- [`planetarium/core/modules/supabase/updater.py`](./planetarium/core/modules/supabase/updater.py.md)
- [`planetarium/core/modules/supabase/wallet.py`](./planetarium/core/modules/supabase/wallet.py.md)
- [`planetarium/core/notification_cron.py`](./planetarium/core/notification_cron.py.md)
- [`planetarium/core/notification_service.py`](./planetarium/core/notification_service.py.md)
- [`planetarium/core/notification_toast.py`](./planetarium/core/notification_toast.py.md)
- [`planetarium/core/operation_log.py`](./planetarium/core/operation_log.py.md)
- [`planetarium/core/oplog.py`](./planetarium/core/oplog.py.md)
- [`planetarium/core/paths.py`](./planetarium/core/paths.py.md)
- [`planetarium/core/planet_painter.py`](./planetarium/core/planet_painter.py.md)
- [`planetarium/core/procedural_texture.py`](./planetarium/core/procedural_texture.py.md)
- [`planetarium/core/reconciliation.py`](./planetarium/core/reconciliation.py.md)
- [`planetarium/core/scheduled_tasks.py`](./planetarium/core/scheduled_tasks.py.md)
- [`planetarium/core/shapes/__init__.py`](./planetarium/core/shapes/__init__.py.md)
- [`planetarium/core/shapes/alien.py`](./planetarium/core/shapes/alien.py.md)
- [`planetarium/core/shapes/black_hole.py`](./planetarium/core/shapes/black_hole.py.md)
- [`planetarium/core/shapes/classic.py`](./planetarium/core/shapes/classic.py.md)
- [`planetarium/core/shapes/classic_20260614_184255_598.py`](./planetarium/core/shapes/classic_20260614_184255_598.py.md)
- [`planetarium/core/shapes/comet.py`](./planetarium/core/shapes/comet.py.md)
- [`planetarium/core/shapes/corvette.py`](./planetarium/core/shapes/corvette.py.md)
- [`planetarium/core/shapes/crystal_alien.py`](./planetarium/core/shapes/crystal_alien.py.md)
- [`planetarium/core/shapes/destroyer.py`](./planetarium/core/shapes/destroyer.py.md)
- [`planetarium/core/shapes/dreadnought.py`](./planetarium/core/shapes/dreadnought.py.md)
- [`planetarium/core/shapes/energy_being.py`](./planetarium/core/shapes/energy_being.py.md)
- [`planetarium/core/shapes/fighter.py`](./planetarium/core/shapes/fighter.py.md)
- [`planetarium/core/shapes/gas_giant.py`](./planetarium/core/shapes/gas_giant.py.md)
- [`planetarium/core/shapes/gas_giant_20260614_184255_426.py`](./planetarium/core/shapes/gas_giant_20260614_184255_426.py.md)
- [`planetarium/core/shapes/ghost_alien.py`](./planetarium/core/shapes/ghost_alien.py.md)
- [`planetarium/core/shapes/grey_alien.py`](./planetarium/core/shapes/grey_alien.py.md)
- [`planetarium/core/shapes/ice_giant.py`](./planetarium/core/shapes/ice_giant.py.md)
- [`planetarium/core/shapes/ice_giant_20260614_184255_207.py`](./planetarium/core/shapes/ice_giant_20260614_184255_207.py.md)
- [`planetarium/core/shapes/interceptor.py`](./planetarium/core/shapes/interceptor.py.md)
- [`planetarium/core/shapes/jellyfish_alien.py`](./planetarium/core/shapes/jellyfish_alien.py.md)
- [`planetarium/core/shapes/lava_planet.py`](./planetarium/core/shapes/lava_planet.py.md)
- [`planetarium/core/shapes/lava_planet_20260614_184255_101.py`](./planetarium/core/shapes/lava_planet_20260614_184255_101.py.md)
- [`planetarium/core/shapes/mars.py`](./planetarium/core/shapes/mars.py.md)
- [`planetarium/core/shapes/mars_20260614_184255_257.py`](./planetarium/core/shapes/mars_20260614_184255_257.py.md)
- [`planetarium/core/shapes/mercury.py`](./planetarium/core/shapes/mercury.py.md)
- [`planetarium/core/shapes/nebula.py`](./planetarium/core/shapes/nebula.py.md)
- [`planetarium/core/shapes/neutron_star.py`](./planetarium/core/shapes/neutron_star.py.md)
- [`planetarium/core/shapes/octopus_alien.py`](./planetarium/core/shapes/octopus_alien.py.md)
- [`planetarium/core/shapes/pluto.py`](./planetarium/core/shapes/pluto.py.md)
- [`planetarium/core/shapes/pulsar.py`](./planetarium/core/shapes/pulsar.py.md)
- [`planetarium/core/shapes/red_giant.py`](./planetarium/core/shapes/red_giant.py.md)
- [`planetarium/core/shapes/reptilian.py`](./planetarium/core/shapes/reptilian.py.md)
- [`planetarium/core/shapes/robot_alien.py`](./planetarium/core/shapes/robot_alien.py.md)
- [`planetarium/core/shapes/saturn.py`](./planetarium/core/shapes/saturn.py.md)
- [`planetarium/core/shapes/scout.py`](./planetarium/core/shapes/scout.py.md)
- [`planetarium/core/shapes/starship.py`](./planetarium/core/shapes/starship.py.md)
- [`planetarium/core/shapes/transporter.py`](./planetarium/core/shapes/transporter.py.md)
- [`planetarium/core/shapes/uranus.py`](./planetarium/core/shapes/uranus.py.md)
- [`planetarium/core/shapes/venus.py`](./planetarium/core/shapes/venus.py.md)
- [`planetarium/core/shapes/white_dwarf.py`](./planetarium/core/shapes/white_dwarf.py.md)
- [`planetarium/core/shapes/wormhole.py`](./planetarium/core/shapes/wormhole.py.md)
- [`planetarium/core/simple_sync.py`](./planetarium/core/simple_sync.py.md)
- [`planetarium/core/storage.py`](./planetarium/core/storage.py.md)
- [`planetarium/core/supabase_client.py`](./planetarium/core/supabase_client.py.md)
- [`planetarium/core/sync_bridge.py`](./planetarium/core/sync_bridge.py.md)
- [`planetarium/core/sync_decorator.py`](./planetarium/core/sync_decorator.py.md)
- [`planetarium/core/sync_integration.py`](./planetarium/core/sync_integration.py.md)
- [`planetarium/core/sync_manager.py`](./planetarium/core/sync_manager.py.md)
- [`planetarium/core/texture_mapper.py`](./planetarium/core/texture_mapper.py.md)
- [`planetarium/core/user_dao.py`](./planetarium/core/user_dao.py.md)
- [`planetarium/core/voice.py`](./planetarium/core/voice.py.md)
- [`planetarium/core/workflow_engine.py`](./planetarium/core/workflow_engine.py.md)
- [`planetarium/services/__init__.py`](./planetarium/services/__init__.py.md)
- [`planetarium/services/ai_chatbot_service.py`](./planetarium/services/ai_chatbot_service.py.md)
- [`planetarium/services/audit_service.py`](./planetarium/services/audit_service.py.md)
- [`planetarium/services/backup_service.py`](./planetarium/services/backup_service.py.md)
- [`planetarium/services/backup_tool.py`](./planetarium/services/backup_tool.py.md)
- [`planetarium/services/barcode_service.py`](./planetarium/services/barcode_service.py.md)
- [`planetarium/services/cache_service.py`](./planetarium/services/cache_service.py.md)
- [`planetarium/services/encryption_service.py`](./planetarium/services/encryption_service.py.md)
- [`planetarium/services/i18n_service.py`](./planetarium/services/i18n_service.py.md)
- [`planetarium/services/image_cache_service.py`](./planetarium/services/image_cache_service.py.md)
- [`planetarium/services/lazy_load_service.py`](./planetarium/services/lazy_load_service.py.md)
- [`planetarium/services/license_service.py`](./planetarium/services/license_service.py.md)
- [`planetarium/services/memory_service.py`](./planetarium/services/memory_service.py.md)
- [`planetarium/services/notification_service.py`](./planetarium/services/notification_service.py.md)
- [`planetarium/services/offline_queue.py`](./planetarium/services/offline_queue.py.md)
- [`planetarium/services/performance_service.py`](./planetarium/services/performance_service.py.md)
- [`planetarium/services/scheduler_service.py`](./planetarium/services/scheduler_service.py.md)
- [`planetarium/services/sync_manager.py`](./planetarium/services/sync_manager.py.md)
- [`planetarium/services/system_tray.py`](./planetarium/services/system_tray.py.md)
- [`planetarium/services/theme_service.py`](./planetarium/services/theme_service.py.md)
- [`planetarium/services/update_service.py`](./planetarium/services/update_service.py.md)
- [`planetarium/shapes/__init__.py`](./planetarium/shapes/__init__.py.md)
- [`planetarium/shapes/alien.py`](./planetarium/shapes/alien.py.md)
- [`planetarium/shapes/black_hole.py`](./planetarium/shapes/black_hole.py.md)
- [`planetarium/shapes/classic.py`](./planetarium/shapes/classic.py.md)
- [`planetarium/shapes/comet.py`](./planetarium/shapes/comet.py.md)
- [`planetarium/shapes/corvette.py`](./planetarium/shapes/corvette.py.md)
- [`planetarium/shapes/crystal_alien.py`](./planetarium/shapes/crystal_alien.py.md)
- [`planetarium/shapes/destroyer.py`](./planetarium/shapes/destroyer.py.md)
- [`planetarium/shapes/dreadnought.py`](./planetarium/shapes/dreadnought.py.md)
- [`planetarium/shapes/energy_being.py`](./planetarium/shapes/energy_being.py.md)
- [`planetarium/shapes/fighter.py`](./planetarium/shapes/fighter.py.md)
- [`planetarium/shapes/gas_giant.py`](./planetarium/shapes/gas_giant.py.md)
- [`planetarium/shapes/ghost_alien.py`](./planetarium/shapes/ghost_alien.py.md)
- [`planetarium/shapes/grey_alien.py`](./planetarium/shapes/grey_alien.py.md)
- [`planetarium/shapes/ice_giant.py`](./planetarium/shapes/ice_giant.py.md)
- [`planetarium/shapes/interceptor.py`](./planetarium/shapes/interceptor.py.md)
- [`planetarium/shapes/jellyfish_alien.py`](./planetarium/shapes/jellyfish_alien.py.md)
- [`planetarium/shapes/lava_planet.py`](./planetarium/shapes/lava_planet.py.md)
- [`planetarium/shapes/mars.py`](./planetarium/shapes/mars.py.md)
- [`planetarium/shapes/mercury.py`](./planetarium/shapes/mercury.py.md)
- [`planetarium/shapes/nebula.py`](./planetarium/shapes/nebula.py.md)
- [`planetarium/shapes/neutron_star.py`](./planetarium/shapes/neutron_star.py.md)
- [`planetarium/shapes/octopus_alien.py`](./planetarium/shapes/octopus_alien.py.md)
- [`planetarium/shapes/pluto.py`](./planetarium/shapes/pluto.py.md)
- [`planetarium/shapes/pulsar.py`](./planetarium/shapes/pulsar.py.md)
- [`planetarium/shapes/red_giant.py`](./planetarium/shapes/red_giant.py.md)
- [`planetarium/shapes/reptilian.py`](./planetarium/shapes/reptilian.py.md)
- [`planetarium/shapes/robot_alien.py`](./planetarium/shapes/robot_alien.py.md)
- [`planetarium/shapes/saturn.py`](./planetarium/shapes/saturn.py.md)
- [`planetarium/shapes/scout.py`](./planetarium/shapes/scout.py.md)
- [`planetarium/shapes/starship.py`](./planetarium/shapes/starship.py.md)
- [`planetarium/shapes/transporter.py`](./planetarium/shapes/transporter.py.md)
- [`planetarium/shapes/uranus.py`](./planetarium/shapes/uranus.py.md)
- [`planetarium/shapes/venus.py`](./planetarium/shapes/venus.py.md)
- [`planetarium/shapes/white_dwarf.py`](./planetarium/shapes/white_dwarf.py.md)
- [`planetarium/shapes/wormhole.py`](./planetarium/shapes/wormhole.py.md)
- [`planetarium/tools/__init__.py`](./planetarium/tools/__init__.py.md)
- [`planetarium/tools/environments/__init__.py`](./planetarium/tools/environments/__init__.py.md)
- [`solar_explorer/__init__.py`](./solar_explorer/__init__.py.md)
- [`solar_explorer/body_data_entries.py`](./solar_explorer/body_data_entries.py.md)
- [`solar_explorer/body_detail_window.py`](./solar_explorer/body_detail_window.py.md)
- [`solar_explorer/body_encyclopedia.py`](./solar_explorer/body_encyclopedia.py.md)
- [`solar_explorer/star_catalog_window.py`](./solar_explorer/star_catalog_window.py.md)
- [`solar_explorer/voice_reader.py`](./solar_explorer/voice_reader.py.md)
- [`test_sync_30_tables.py`](./test_sync_30_tables.py.md)
- [`tools/clean_package.py`](./tools/clean_package.py.md)
- [`tools/pack_build.py`](./tools/pack_build.py.md)
- [`verify_both.py`](./verify_both.py.md)
