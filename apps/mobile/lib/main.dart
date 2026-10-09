import 'package:flutter/material.dart';

void main() {
  runApp(const AppiApp());
}

class AppiApp extends StatelessWidget {
  const AppiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Appi',
      theme: ThemeData.dark(useMaterial3: true),
      home: const AppiShell(),
    );
  }
}

class AppiShell extends StatefulWidget {
  const AppiShell({super.key});

  @override
  State<AppiShell> createState() => _AppiShellState();
}

class _AppiShellState extends State<AppiShell> {
  int index = 0;
  String orb = 'Idle';

  static const destinations = [
    'Home',
    'Voice',
    'Tasks',
    'Devices',
    'Connections',
    'Approvals',
    'Activity',
    'Settings',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Appi · ${destinations[index]}')),
      body: index == 0 || index == 1 ? _orb() : _placeholder(destinations[index]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index.clamp(0, 4),
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.mic_none), label: 'Voice'),
          NavigationDestination(icon: Icon(Icons.task_alt), label: 'Tasks'),
          NavigationDestination(icon: Icon(Icons.devices), label: 'Devices'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), label: 'More'),
        ],
      ),
    );
  }

  Widget _orb() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          GestureDetector(
            onTap: () {
              const states = ['Idle', 'Listening', 'Thinking', 'Acting', 'Waiting for approval', 'Done'];
              setState(() => orb = states[(states.indexOf(orb) + 1) % states.length]);
            },
            child: CircleAvatar(
              radius: 72,
              backgroundColor: const Color(0xFF38BDF8),
              child: Text(orb, textAlign: TextAlign.center, style: const TextStyle(color: Colors.black)),
            ),
          ),
          const SizedBox(height: 24),
          const Text('Native Android/iOS runtimes are not implemented in this milestone.'),
          TextButton(
            onPressed: () => setState(() => index = 4),
            child: const Text('Connections · Approvals · Activity · Settings'),
          ),
        ],
      ),
    );
  }

  Widget _placeholder(String title) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(title, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        const Text('This Flutter shell is UI only. Pair a desktop runtime for real actions.'),
        const SizedBox(height: 24),
        ...['Connections', 'Approvals', 'Activity', 'Settings'].map(
          (label) => ListTile(
            title: Text(label),
            onTap: () => setState(() => index = destinations.indexOf(label)),
          ),
        ),
      ],
    );
  }
}
