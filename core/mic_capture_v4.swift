import AVFoundation
import AppKit

// 必须在 NSApplication.shared 之前初始化
let app = NSApplication.shared
app.setActivationPolicy(.accessory) // 不显示 Dock 图标，但可以弹窗

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // 在主线程请求权限
        AVAudioApplication.requestRecordPermission { granted in
            DispatchQueue.main.async {
                let status: String
                if granted {
                    status = "GRANTED"
                } else {
                    status = "DENIED"
                }
                print("PERMISSION_RESULT: \(status)")
                
                // 给用户2秒看结果，然后退出
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    NSApp.terminate(nil)
                }
            }
        }
    }
}

let delegate = AppDelegate()
app.delegate = delegate
app.run()
