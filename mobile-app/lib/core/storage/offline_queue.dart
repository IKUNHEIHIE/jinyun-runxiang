import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:dio/dio.dart';
import '../network/api_client.dart';

class OfflineSyncManager {
  static final OfflineSyncManager _instance = OfflineSyncManager._internal();
  factory OfflineSyncManager() => _instance;
  OfflineSyncManager._internal();

  final List<Map<String, dynamic>> _inMemoryQueue = [];
  final Uuid _uuid = const Uuid();

  /// 弱网或断网时，将学习进度写入本地队列
  void enqueueProgressEvent({
    required int courseId,
    required int chapterId,
    required int positionSeconds,
    required int durationSeconds,
    required bool completed,
  }) {
    final event = {
      'event_id': _uuid.v4(),
      'event_type': 'PROGRESS_UPDATE',
      'payload': {
        'course_id': courseId,
        'chapter_id': chapterId,
        'position_seconds': positionSeconds,
        'duration_seconds': durationSeconds,
        'completed': completed,
      },
      'event_time': DateTime.now().toIso8601String(),
    };
    _inMemoryQueue.add(event);
  }

  /// 恢复网络时，自动批量上报同步
  Future<bool> flushQueue() async {
    if (_inMemoryQueue.isEmpty) return true;

    try {
      final response = await ApiClient().dio.post(
        '/courses/sync-offline',
        data: {'events': _inMemoryQueue},
      );

      if (response.statusCode == 200 && response.data['code'] == 0) {
        final syncedIds = Set<String>.from(
          response.data['data']['success_event_ids'] ?? const <String>[],
        );
        _inMemoryQueue.removeWhere((event) => syncedIds.contains(event['event_id']));
        return _inMemoryQueue.isEmpty;
      }
    } catch (e) {
      // 网络仍然不可用，保留在队列中等待下次重试
      return false;
    }
    return false;
  }

  int get pendingCount => _inMemoryQueue.length;
}
