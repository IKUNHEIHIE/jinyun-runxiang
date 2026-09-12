import 'package:flutter/material.dart';
import 'app/theme.dart';
import 'features/home/home_page.dart';
import 'features/course/course_hall_page.dart';
import 'features/ai_workshop/shadow_puppet_page.dart';
import 'features/community/community_feed_page.dart';
import 'features/teacher/teacher_workbench_page.dart';
import 'features/device/embodied_device_page.dart';

void main() {
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
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  // 五大一级入口 (首页、小课堂、AI工坊、社区、教师/我的)
  final List<Widget> _pages = const [
    HomePage(),
    CourseHallPage(),
    ShadowPuppetPage(),
    CommunityFeedPage(),
    TeacherWorkbenchPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
