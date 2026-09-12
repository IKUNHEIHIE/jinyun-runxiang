import 'dart:async';
import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../core/network/api_client.dart';

class ShadowPuppetPage extends StatefulWidget {
  const ShadowPuppetPage({super.key});

  @override
  State<ShadowPuppetPage> createState() => _ShadowPuppetPageState();
}

class _ShadowPuppetPageState extends State<ShadowPuppetPage> {
  String _selectedRole = '武旦·女将';
  final TextEditingController _promptController = TextEditingController(text: '身披大红战袍，头戴七星额子，手执红缨枪，英姿飒爽');
  
  bool _isGenerating = false;
  int _progress = 0;
  String _statusText = '';
  Map<String, dynamic>? _resultData;

  final List<String> _roles = ['生角·书生', '旦角·小姐', '武旦·女将', '净角·花脸', '丑角·风趣老汉', '神话·孙悟空'];
  final List<String> _promptChips = ['穆桂英天门阵', '齐天大圣踏祥云', '津门海河水师卫士', '红楼金陵巧姑娘'];

  Future<void> _startGeneration() async {
    setState(() {
      _isGenerating = true;
      _progress = 15;
      _statusText = 'AI 正在分析非遗皮影刀法与镂空纹样...';
      _resultData = null;
    });

    try {
      final res = await ApiClient().dio.post('/ai/tasks', data: {
        'tool_type': 'SHADOW_PUPPET',
        'input_payload': {
          'role_type': _selectedRole,
          'prompt': _promptController.text,
        }
      });

      if (res.statusCode == 200 && res.data['code'] == 0) {
        final taskId = res.data['data']['task_id'];
        _pollTask(taskId);
      }
    } catch (e) {
      setState(() {
        _isGenerating = false;
        _statusText = '提交失败，请稍后重试';
      });
    }
  }

  void _pollTask(String taskId) {
    Timer.periodic(const Duration(seconds: 1), (timer) async {
      try {
        final res = await ApiClient().dio.get('/ai/tasks/$taskId');
        if (res.statusCode == 200 && res.data['code'] == 0) {
          final data = res.data['data'];
          final status = data['status'];
          setState(() {
            _progress = data['progress'] ?? 50;
            _statusText = status == 'SUCCESS' ? '生成完成！' : '正在合成津派古法镂空刀痕与驴皮透明质感...';
          });

          if (status == 'SUCCESS') {
            timer.cancel();
            setState(() {
              _isGenerating = false;
              _resultData = data['result'];
            });
          } else if (status == 'FAILED' || status == 'CANCELLED') {
            timer.cancel();
            setState(() {
              _isGenerating = false;
              _statusText = '生成失败，请重试';
            });
          }
        }
      } catch (e) {
        timer.cancel();
        setState(() => _isGenerating = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI皮影工坊', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 步骤 01：选择角色行当
          const Text('01 选择角色行当', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.primaryDark)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: _roles.map((r) {
              final isSelected = _selectedRole == r;
              return ChoiceChip(
                label: Text(r),
                selected: isSelected,
                selectedColor: AppTheme.primary,
                labelStyle: TextStyle(color: isSelected ? Colors.white : AppTheme.textPrimary, fontSize: 12),
                onSelected: (val) {
                  if (val) setState(() => _selectedRole = r);
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 20),

          // 步骤 02：输入设计灵感
          const Text('02 描述人物神态与服饰', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.primaryDark)),
          const SizedBox(height: 8),
          TextField(
            controller: _promptController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: '例如：身披战袍，头戴盔甲，线条分明...',
              fillColor: Colors.white,
              filled: true,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: _promptChips.map((chip) {
              return ActionChip(
                label: Text(chip, style: const TextStyle(fontSize: 11)),
                backgroundColor: AppTheme.paper,
                onPressed: () {
                  _promptController.text = '天津传统皮影角色：$chip，服饰配饰纹样精美。';
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 20),

          // 步骤 03：开始生成按钮
          ElevatedButton(
            onPressed: _isGenerating ? null : _startGeneration,
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(double.infinity, 50),
              backgroundColor: AppTheme.primary,
            ),
            child: _isGenerating
                ? Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                      const SizedBox(width: 12),
                      Text('生成中 ($_progress%)...'),
                    ],
                  )
                : const Text('✨ 立即生成非遗皮影角色', style: TextStyle(fontSize: 16)),
          ),

          if (_isGenerating) ...[
            const SizedBox(height: 12),
            LinearProgressIndicator(value: _progress / 100.0, color: AppTheme.accentGold, backgroundColor: Colors.white),
            const SizedBox(height: 6),
            Text(_statusText, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
          ],

          const SizedBox(height: 24),

          // 步骤 04：生成结果成果展示
          if (_resultData != null) ...[
            const Text('04 生成成果与多模态导出', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.primaryDark)),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.network(_resultData!['colored_image_url'], height: 260, width: double.infinity, fit: BoxFit.cover),
                    ),
                    const SizedBox(height: 12),
                    Text(_resultData!['role_type'] ?? '皮影角色', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.primary)),
                    const SizedBox(height: 6),
                    Text(_resultData!['description'] ?? '', style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4)),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.print, size: 18),
                            label: const Text('A4打印纸样'),
                            onPressed: () {
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已导出A4激光/手工雕镂剪切模板PDF')));
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton.icon(
                            icon: const Icon(Icons.share, size: 18),
                            label: const Text('发布到社区'),
                            onPressed: () {
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('作品已成功发布至非遗美育广场！')));
                            },
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
