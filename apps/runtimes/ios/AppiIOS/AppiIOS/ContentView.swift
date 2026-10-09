import SwiftUI

struct ContentView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Appi")
                    .font(.largeTitle.bold())
                Text("iPhone placeholder")
                    .font(.title3)
                    .foregroundStyle(.secondary)
                Text(
                    "This app does not control other iPhone apps, files, Safari, or the phone assistant. " +
                    "iOS blocks that (OS Restricted).\n\n" +
                    "The working assistant is the Windows background runtime. Say Appi there after you pair the laptop.\n\n" +
                    "Later this app may use App Intents, Shortcuts, notifications, and files you explicitly share. " +
                    "It will never bypass Face ID, passcodes, or other apps’ security screens."
                )
                .font(.body)
            }
            .padding(24)
        }
    }
}
