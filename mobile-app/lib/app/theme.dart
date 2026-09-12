import 'package:flutter/material.dart';

class AppTheme {
  // 3.1 视觉设计系统色彩 Token (依据UI设计文档严格配置)
  static const Color primary = Color(0xFF8B4A2F);       // 主品牌红褐色/选中态
  static const Color primaryDark = Color(0xFF63351F);   // 深色标题/重要强调
  static const Color accentGold = Color(0xFFD6A85C);    // 能量值、徽章、文化装饰金
  static const Color paper = Color(0xFFF8F4EC);         // 页面大背景宣纸质感
  static const Color surface = Color(0xFFFFFFFF);       // 卡片、弹窗
  static const Color textPrimary = Color(0xFF2F2925);   // 主标题/正文
  static const Color textSecondary = Color(0xFF776D65); // 辅助说明/时间标签
  static const Color success = Color(0xFF4D8B63);       // 完成、通过、已解锁
  static const Color warning = Color(0xFFC4863A);       // 待审核、注意
  static const Color danger = Color(0xFFB64A44);        // 错误、违规、下架

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: paper,
      colorScheme: const ColorScheme.light(
        primary: primary,
        secondary: accentGold,
        surface: surface,
        error: danger,
        onPrimary: Colors.white,
        onSurface: textPrimary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: paper,
        foregroundColor: primaryDark,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: primaryDark,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
      cardTheme: CardTheme(
        color: surface,
        elevation: 0.5,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(88, 44),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: primary,
        unselectedItemColor: textSecondary,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }
}
