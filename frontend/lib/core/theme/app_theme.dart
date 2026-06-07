import 'package:flutter/material.dart';

class AppTheme {
  // 浅青/雾蓝主色（低饱和冷色调）
  static const _primary = Color(0xFF5B9AA8); // 雾蓝
  static const _secondary = Color(0xFF7FB3BE); // 浅青
  static const _surface = Color(0xFFF5F5F5); // 哑光灰底
  static const _textPrimary = Color(0xFF1A1A1A); // 正文黑

  static ThemeData light() => ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: _surface,
        colorScheme: ColorScheme.light(
          primary: _primary,
          secondary: _secondary,
          surface: _surface,
          surfaceContainerHighest: const Color(0xFFE8E8E8),
          primaryContainer: _primary.withValues(alpha: 0.15),
          secondaryContainer: _secondary.withValues(alpha: 0.12),
          onPrimary: Colors.white,
          onSurface: _textPrimary,
          onSurfaceVariant: const Color(0xFF666666),
        ),
        textTheme: const TextTheme(
          headlineSmall: TextStyle(fontWeight: FontWeight.w700, color: _primary),
          titleLarge: TextStyle(fontWeight: FontWeight.w700, color: _primary),
          titleMedium: TextStyle(fontWeight: FontWeight.w600, color: _textPrimary),
          bodyLarge: TextStyle(color: _textPrimary),
          bodyMedium: TextStyle(color: _textPrimary),
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: _primary,
          foregroundColor: Colors.white,
        ),
      );

  static ThemeData dark() => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(seedColor: _primary, brightness: Brightness.dark),
      );
}