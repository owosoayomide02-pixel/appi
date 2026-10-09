import SwiftUI
import AppIntents

struct OpenAppiIntent: AppIntent {
    static var title: LocalizedStringResource = "Open Appi"
    static var description = IntentDescription("Opens the Appi iPhone placeholder. Device control of other apps is OS Restricted.")
    static var openAppWhenRun: Bool = true

    func perform() async throws -> some IntentResult {
        .result()
    }
}

struct AppiShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: OpenAppiIntent(),
            phrases: [
                "Open \(.applicationName)",
                "Open Appi"
            ],
            shortTitle: "Open Appi",
            systemImageName: "waveform"
        )
    }
}
