import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../core/storage/offline_queue.dart';

class LoginPage extends StatefulWidget {
  final void Function(BuildContext) onSignedIn;
  const LoginPage({super.key, required this.onSignedIn});
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  Future<void> _login() async {
    setState(() { _busy = true; _error = null; });
    try {
      final response = await ApiClient().dio.post('/auth/login', data: {
        'username': _username.text.trim(), 'password': _password.text,
      });
      if (response.data['code'] != 0) throw StateError(response.data['message'] ?? '登录失败');
      final data = response.data['data'];
      final user = data['user'];
      ApiClient().setToken(data['token'], user['id'], user['role_code']);
      _password.clear();
      await OfflineSyncManager().flushQueue();
      if (mounted) widget.onSignedIn(context);
    } catch (_) {
      if (mounted) setState(() => _error = '登录失败，请检查账号、密码与网络');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() { _username.dispose(); _password.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('登录津韵润乡')),
    body: Padding(padding: const EdgeInsets.all(24), child: Column(children: [
      TextField(controller: _username, decoration: const InputDecoration(labelText: '用户名'),
        autofillHints: const [AutofillHints.username]),
      TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: '密码'),
        autofillHints: const [AutofillHints.password], onSubmitted: (_) => _busy ? null : _login()),
      const SizedBox(height: 24),
      if (ApiClient.apiBaseUrl.isEmpty) const Text('请在构建时通过 API_BASE_URL 配置服务地址'),
      if (_error != null) Text(_error!),
      ElevatedButton(onPressed: _busy || ApiClient.apiBaseUrl.isEmpty ? null : _login,
        child: Text(_busy ? '登录中…' : '登录')),
    ])),
  );
}
