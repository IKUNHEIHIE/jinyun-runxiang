import 'dart:async';
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'features/auth/login_page.dart';
import 'core/network/api_client.dart';
import 'core/storage/offline_queue.dart';
import 'app/theme.dart';
import 'features/home/home_page.dart';
import 'features/course/course_hall_page.dart';
import 'features/ai_workshop/shadow_puppet_page.dart';
import 'features/community/community_feed_page.dart';
import 'features/teacher/teacher_workbench_page.dart';
import 'features/device/embodied_device_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  await Hive.openBox<String>('offline_progress');
  runApp(const JinyunRunxiangApp());
}

class JinyunRunxiangApp extends StatelessWidget {
  const JinyunRunxiangApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '津韵润乡',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: LoginPage(onSignedIn: (context) {
        Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const MainNavigationScreen()));
      }),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> with WidgetsBindingObserver {
  Timer? _syncTimer;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    ApiClient().onUnauthorized = _openLogin;
    _syncTimer = Timer.periodic(const Duration(seconds: 30), (_) => OfflineSyncManager().flushQueue());
  }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) OfflineSyncManager().flushQueue();
  }
  @override
  void dispose() {
    _syncTimer?.cancel();
    ApiClient().onUnauthorized = null;
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
  bool _leaving = false;
  void _openLogin() {
    if (!mounted || _leaving) return;
    _leaving = true;
    ApiClient().clearToken();
    Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => LoginPage(
      onSignedIn: (context) => Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const MainNavigationScreen())),
    )), (_) => false);
  }
  Future<void> _logout() async {
    try { await ApiClient().dio.post('/auth/logout'); } catch (_) {}
    _openLogin();
  }
  int _currentIndex = 0;

  // 五大一级入口 (首页、小课堂、AI工坊、社区、教师/我的)
  late final List<Widget> _pages = [
    HomePage(),
    CourseHallPage(),
    ShadowPuppetPage(),
    CommunityFeedPage(),
    ApiClient().roleCode == 'TEACHER' || ApiClient().roleCode == 'ADMIN'
        ? const TeacherWorkbenchPage()
        : const Scaffold(body: Center(child: Text('学习进度会自动保存并同步'))),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton.small(onPressed: _logout,
        tooltip: '退出登录', child: const Icon(Icons.logout)),
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: AppTheme.primary,
        unselectedItemColor: AppTheme.textSecondary,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: '首页',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.school_outlined),
            activeIcon: Icon(Icons.school),
            label: '小课堂',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.brush_outlined),
            activeIcon: Icon(Icons.brush),
            label: 'AI工坊',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.forum_outlined),
            activeIcon: Icon(Icons.forum),
            label: '社区',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.co_present_outlined),
            activeIcon: Icon(Icons.co_present),
            label: '工作台',
          ),
        ],
      ),
    );
  }
}
