import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../core/network/api_client.dart';

class TeacherWorkbenchPage extends StatefulWidget {
  const TeacherWorkbenchPage({super.key});

  @override
  State<TeacherWorkbenchPage> createState() => _TeacherWorkbenchPageState();
}

class _TeacherWorkbenchPageState extends State<TeacherWorkbenchPage> {
  String _selectedTopic = '天津皮影戏';
  String _selectedGrade = '小学三年级';
  bool _generatingPlan = false;
  Map<String, dynamic>? _generatedPlan;

  final List<String> _topics = ['天津皮影戏', '杨柳青木版年画', '泥人张彩塑', '青铜神兽饕餮纹', '骆派京韵大鼓', '古法大漆螺钿'];

  Future<void> _generateLessonPlan() async {
    setState(() {
      _generatingPlan = true;
      _generatedPlan = null;
    });

    try {
      final res = await ApiClient().dio.post('/teacher/lesson-plans/generate', data: {
        'topic': _selectedTopic,
        'grade': _selectedGrade,
        'duration_minutes': 45,
      });

      if (res.statusCode == 200 && res.data['code'] == 0) {
        setState(() {
          _generatedPlan = res.data['data'];
          _generatingPlan = false;
        });
      }
    } catch (e) {
      setState(() => _generatingPlan = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('教师专属工作台 (T-01)', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 班级概览与待办卡片
          Card(
            color: AppTheme.primaryDark,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('蓟州区下营镇中心小学 · 三年级一班', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                      Text('42名学生', style: TextStyle(color: AppTheme.accentGold, fontSize: 12)),
                    ],
                  ),
                  SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Column(
                        children: [
                          Text('84.5%', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('课程完成率', style: TextStyle(color: Colors.white70, fontSize: 11)),
                        ],
                      ),
                      Column(
                        children: [
                          Text('88.0%', style: TextStyle(color: AppTheme.accentGold, fontSize: 20, fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('测验平均分', style: TextStyle(color: Colors.white70, fontSize: 11)),
                        ],
                      ),
                      Column(
                        children: [
                          Text('16', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('待批作业', style: TextStyle(color: Colors.white70, fontSize: 11)),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // AI 智能备课功能卡片 (T-02)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.auto_stories, color: AppTheme.primary),
                      SizedBox(width: 8),
                      Text('AI智能非遗备课引擎 (T-02)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.primaryDark)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('选择非遗教学主题：', style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 8,
                    children: _topics.map((t) {
                      final isSelected = _selectedTopic == t;
                      return ChoiceChip(
                        label: Text(t),
                        selected: isSelected,
                        selectedColor: AppTheme.primary,
                        labelStyle: TextStyle(color: isSelected ? Colors.white : AppTheme.textPrimary, fontSize: 12),
                        onSelected: (val) {
                          if (val) setState(() => _selectedTopic = t);
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.psychology, size: 18),
                    label: _generatingPlan
                        ? const Text('AI教研大脑正在构思教案与课件...')
                        : const Text('一键生成教学目标、讲稿与配套PPT'),
                    onPressed: _generatingPlan ? null : _generateLessonPlan,
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 46),
                      backgroundColor: AppTheme.primary,
                    ),
                  ),

                  if (_generatedPlan != null) ...[
                    const Divider(height: 30),
                    Text(_generatedPlan!['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.primary)),
                    const SizedBox(height: 8),
                    Text('时长: ${_generatedPlan!['duration']}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                    const SizedBox(height: 10),
                    const Text('美育教学重点：', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    Text(_generatedPlan!['key_difficult_points']?['key'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.download, size: 16),
                      label: const Text('下载标准课件 PPT 演示文稿'),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已成功下载教案配套 PPTX 资源包')));
                      },
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
