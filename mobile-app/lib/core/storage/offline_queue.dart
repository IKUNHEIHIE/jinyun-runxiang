import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:hive/hive.dart';
import '../network/api_client.dart';

class OfflineSyncManager {
  static final OfflineSyncManager _instance = OfflineSyncManager._internal();
  factory OfflineSyncManager() => _instance;
  OfflineSyncManager._internal();

  final Uuid _uuid = const Uuid();
  bool _flushing = false;
  Box<String> get _box => Hive.box<String>('offline_progress');
  List<Map<String, dynamic>> _read(int userId) {
    final raw = _box.get('$userId');
    if (raw == null) return [];
    return (jsonDecode(raw) as List).map((item) => Map<String, dynamic>.from(item)).toList();
  }

  Future<void> enqueueProgressEvent({
    required int courseId, required int chapterId,
    required int positionSeconds, required int durationSeconds,
    required bool completed,
  }) async {
    final userId = ApiClient().userId;
    if (userId == null) throw StateError('请先登录');
    final queue = _read(userId);
    queue.add({
      'event_id': _uuid.v4(), 'event_type': 'PROGRESS_UPDATE',
      'payload': {'course_id': courseId, 'chapter_id': chapterId,
        'position_seconds': positionSeconds, 'duration_seconds': durationSeconds,
        'completed': completed},
      'event_time': DateTime.now().toUtc().toIso8601String(),
    });
    await _box.put('$userId', jsonEncode(queue));
  }

  Future<bool> flushQueue() async {
    final userId = ApiClient().userId;
    if (userId == null || _flushing) return false;
    final snapshot = _read(userId).take(100).toList();
    if (snapshot.isEmpty) return true;
    _flushing = true;
    try {
      final response = await ApiClient().dio.post('/courses/sync-offline', data: {'events': snapshot});
      if (response.statusCode != 200 || response.data['code'] != 0) return false;
      final accepted = Set<String>.from(response.data['data']['success_event_ids'] ?? []);
      final submitted = snapshot.map((event) => event['event_id'] as String).toSet();
      final confirmed = accepted.intersection(submitted);
      // Read again after awaiting the response: preserve events added during the upload.
      final remaining = _read(userId)..removeWhere((event) => confirmed.contains(event['event_id']));
      await _box.put('$userId', jsonEncode(remaining));
      return remaining.isEmpty;
    } catch (_) {
      return false;
    } finally {
      _flushing = false;
    }
  }

  int get pendingCount {
    final userId = ApiClient().userId;
    return userId == null ? 0 : _read(userId).length;
  }
}
