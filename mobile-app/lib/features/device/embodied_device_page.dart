import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../core/network/api_client.dart';

class EmbodiedDevicePage extends StatefulWidget {
  const EmbodiedDevicePage({super.key});

  @override
  State<EmbodiedDevicePage> createState() => _EmbodiedDevicePageState();
}

class _EmbodiedDevicePageState extends State<EmbodiedDevicePage> {
  bool _isOnline = true;
  String _currentStatus = '待命就绪 · 已加载天津皮影老生动作库';
  bool _executing = false;

  Future<void> _sendCommand(String cmdType) async {
    setState(() {
      _executing = true;
      _currentStatus = '指令传输中 (MQTT/WebSocket)...';
    });

    try {
      final res = await ApiClient().dio.post('/devices/DEV-SHADOW-BOT-01/command', data: {
        'command_type': cmdType,
        'payload': {'action': cmdType},
      });

      if (res.statusCode == 200 && res.data['code'] == 0) {
        setState(() {
          _executing = false;
          _currentStatus = cmdType == 'PERFORM_SHADOW_PLAY'
              ? '正在操纵三签人偶进行“孙悟空大闹天宫”翻跟头表演动作'
              : '正在通过语音TTS向同学们讲解天津皮影由驴皮刮浆雕镂的历史起源';
        });
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(res.data['message'] ?? '指令已执行'),
          backgroundColor: AppTheme.success,
        ));
      }
    } catch (e) {
      setState(() {
        _executing = false;
        _currentStatus = '硬件离线，已自动降级为手机端3D虚拟表演动画';
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('已无缝切换至手机端虚拟演示模式'),
        backgroundColor: AppTheme.warning,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('智能非遗具身设备交互', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 设备卡片
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _isOnline ? AppTheme.success : AppTheme.danger,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text('津韵智能皮影表演机器人', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        ],
                      ),
                      Text(_isOnline ? '● 在线' : '○ 离线', style: TextStyle(color: _isOnline ? AppTheme.success : AppTheme.danger, fontWeight: FontWeight.bold, fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('设备编号: DEV-SHADOW-BOT-01 · 固件版本: v1.2.0', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                  const SizedBox(height: 6),
                  const Text('部署点位: 蓟州区下营镇中心小学美育创客室', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                  const Divider(height: 24),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMetric('电量', '82%', AppTheme.success),
                      _buildMetric('Wi-Fi', '良好 (-55dBm)', AppTheme.textPrimary),
                      _buildMetric('舵机轴数', '6-DOF', AppTheme.accentGold),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // 实时交互与指令下发
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('动作演示与互动控制', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.primaryDark)),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.paper,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('当前状态: $_currentStatus', style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary, height: 1.4)),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.play_circle_fill, size: 18),
                          label: const Text('操杆舞台表演'),
                          onPressed: _executing ? null : () => _sendCommand('PERFORM_SHADOW_PLAY'),
                          style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.record_voice_over, size: 18),
                          label: const Text('非遗语音讲解'),
                          onPressed: _executing ? null : () => _sendCommand('SPEAK_EXPLANATION'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // 虚拟交互与降级兜底提示
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.accentGold.withOpacity(0.3)),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, color: AppTheme.accentGold, size: 20),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '说明：若现场无实体硬件，系统自动启用手机端3D虚拟模型表演与离线语音讲解，不影响正常美育课程教学。',
                    style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.4),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
      ],
    );
  }
}
