import 'dart:async';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../core/network/api_client.dart';
import '../../core/storage/offline_queue.dart';

class CourseLearningPage extends StatefulWidget {
  final int courseId;
  const CourseLearningPage({super.key, required this.courseId});
  @override
  State<CourseLearningPage> createState() => _CourseLearningPageState();
}

class _CourseLearningPageState extends State<CourseLearningPage> {
  List<dynamic> _chapters = [];
  Map<String, dynamic>? _chapter;
  VideoPlayerController? _player;
  Timer? _saveTimer;
  String? _error;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
    _saveTimer = Timer.periodic(const Duration(seconds: 15), (_) => _save());
  }
  Future<void> _load() async {
    try {
      final response = await ApiClient().dio.get('/courses/${widget.courseId}');
      if (response.data['code'] != 0) throw StateError('课程不存在');
      _chapters = response.data['data']['chapters'] ?? [];
      if (_chapters.isNotEmpty) await _select(Map<String, dynamic>.from(_chapters.first));
      if (mounted) setState(() {});
    } catch (_) { if (mounted) setState(() => _error = '课程加载失败，请检查网络'); }
  }
  Future<void> _select(Map<String, dynamic> chapter) async {
    await _save();
    await _player?.dispose();
    _chapter = chapter;
    final base = Uri.parse(ApiClient.apiBaseUrl);
    final url = base.resolve(chapter['video_url'] as String);
    final player = VideoPlayerController.networkUrl(url);
    _player = player;
    try {
      await player.initialize();
      final progress = chapter['progress'];
      if (progress is Map && progress['position_seconds'] is int) {
        await player.seekTo(Duration(seconds: progress['position_seconds']));
      }
      if (mounted) setState(() => _error = null);
    } catch (_) { if (mounted) setState(() => _error = '视频加载失败'); }
  }
  Future<void> _save() async {
    final player = _player;
    final chapter = _chapter;
    if (_saving || player == null || chapter == null || !player.value.isInitialized) return;
    final position = player.value.position.inSeconds;
    final duration = player.value.duration.inSeconds;
    if (duration <= 0) return;
    _saving = true;
    try {
      await OfflineSyncManager().enqueueProgressEvent(courseId: widget.courseId,
        chapterId: chapter['id'], positionSeconds: position, durationSeconds: duration,
        completed: position >= duration * 0.95);
      await OfflineSyncManager().flushQueue();
    } finally { _saving = false; }
  }
  @override
  void dispose() {
    _saveTimer?.cancel();
    // Enqueue captures the progress before the player is disposed.
    unawaited(_save());
    _player?.dispose();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('课程学习')),
    body: ListView(children: [
      if (_error != null) Padding(padding: const EdgeInsets.all(16), child: Text(_error!)),
      if (_player?.value.isInitialized ?? false) ...[
        AspectRatio(aspectRatio: _player!.value.aspectRatio, child: VideoPlayer(_player!)),
        IconButton(icon: Icon(_player!.value.isPlaying ? Icons.pause : Icons.play_arrow), onPressed: () {
          setState(() { _player!.value.isPlaying ? _player!.pause() : _player!.play(); });
        }),
      ],
      for (final chapter in _chapters) ListTile(title: Text(chapter['title']),
        onTap: () => _select(Map<String, dynamic>.from(chapter))),
      const Padding(padding: EdgeInsets.all(16), child: Text('学习进度自动保存，恢复网络后同步。')),
    ]),
  );
}
