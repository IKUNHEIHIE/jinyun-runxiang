import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../core/network/api_client.dart';
import 'course_learning_page.dart';

class CourseHallPage extends StatefulWidget {
  const CourseHallPage({super.key});

  @override
  State<CourseHallPage> createState() => _CourseHallPageState();
}

class _CourseHallPageState extends State<CourseHallPage> {
  String _selectedAge = '';
  String _selectedCat = '';
  List<dynamic> _courses = [];
  bool _loading = true;

  final List<Map<String, String>> _categories = [
    {'code': '', 'name': '全部非遗'},
    {'code': 'SHADOW_PUPPET', 'name': '津门皮影'},
    {'code': 'PAINTING', 'name': '杨柳青年画'},
    {'code': 'CLAY', 'name': '泥人张彩塑'},
    {'code': 'BRONZE', 'name': '青铜纹样'},
    {'code': 'BALLAD', 'name': '京韵大鼓'},
    {'code': 'LACQUER', 'name': '古法大漆'},
  ];

  final List<Map<String, String>> _ageGroups = [
    {'code': '', 'name': '全学段'},
    {'code': 'PRIMARY_LOW', 'name': '低年级·动画体验'},
    {'code': 'PRIMARY_HIGH', 'name': '高年级·手工实践'},
    {'code': 'JUNIOR', 'name': '初中·项目研学'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchCourses();
  }

  Future<void> _fetchCourses() async {
    setState(() => _loading = true);
    try {
      String path = '/courses?page=1&pageSize=20';
      if (_selectedCat.isNotEmpty) path += '&category=$_selectedCat';
      if (_selectedAge.isNotEmpty) path += '&age_group=$_selectedAge';

      final res = await ApiClient().dio.get(path);
      if (res.statusCode == 200 && res.data['code'] == 0) {
        setState(() {
          _courses = res.data['data']['list'] ?? [];
          _loading = false;
        });
      }
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('非遗小课堂', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // 第一层筛选：非遗门类
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: _categories.map((c) {
                final isSelected = _selectedCat == c['code'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(c['name']!),
                    selected: isSelected,
                    selectedColor: AppTheme.primary,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : AppTheme.textPrimary,
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                    onSelected: (val) {
                      setState(() => _selectedCat = val ? c['code']! : '');
                      _fetchCourses();
                    },
                  ),
                );
              }).toList(),
            ),
          ),

          // 第二层筛选：适用学段
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: _ageGroups.map((a) {
                final isSelected = _selectedAge == a['code'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(a['name']!),
                    selected: isSelected,
                    checkmarkColor: AppTheme.accentGold,
                    labelStyle: TextStyle(
                      fontSize: 11,
                      color: isSelected ? AppTheme.primaryDark : AppTheme.textSecondary,
                    ),
                    onSelected: (val) {
                      setState(() => _selectedAge = val ? a['code']! : '');
                      _fetchCourses();
                    },
                  ),
                );
              }).toList(),
            ),
          ),

          const SizedBox(height: 8),

          // 课程列表
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                : _courses.isEmpty
                    ? const Center(child: Text('暂无相关课程', style: TextStyle(color: AppTheme.textSecondary)))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _courses.length,
                        itemBuilder: (context, index) {
                          final item = _courses[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                ClipRRect(
                                  borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                                  child: Image.network(item['cover_url'], height: 160, width: double.infinity, fit: BoxFit.cover),
                                ),
                                Padding(
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(item['title'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textPrimary)),
                                      const SizedBox(height: 4),
                                      Text(item['subtitle'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                      const SizedBox(height: 10),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text('⏱️ ${item['duration_minutes']} 分钟 · ⚡ +${item['energy_reward']} 能量', style: const TextStyle(fontSize: 12, color: AppTheme.accentGold, fontWeight: FontWeight.w600)),
                                          ElevatedButton(
                                            onPressed: () {
                                              Navigator.of(context).push(MaterialPageRoute(builder: (_) => CourseLearningPage(courseId: item['id'])));
                                            },
                                            child: const Text('开始学习'),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
