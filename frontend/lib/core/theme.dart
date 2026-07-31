import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color primary     = Color(0xFF1D9E75);
  static const Color primaryDark = Color(0xFF0F6E56);
  static const Color background  = Color(0xFF0F1117);
  static const Color surface     = Color(0xFF1A1D27);
  static const Color surface2    = Color(0xFF242836);
  static const Color amber       = Color(0xFFEF9F27);
  static const Color blue        = Color(0xFF185FA5);
  static const Color red         = Color(0xFFE24B4A);
  static const Color textPrimary = Color(0xFFE8E6DF);
  static const Color textSecond  = Color(0xFF9B9994);
  static const Color border      = Color(0xFF2E3142);

  static ThemeData get darkTheme => ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: background,
    primaryColor: primary,
    colorScheme: const ColorScheme.dark(
      primary:   primary,
      secondary: amber,
      surface:   surface,
      error:     red,
    ),
    textTheme: GoogleFonts.interTextTheme(
      ThemeData.dark().textTheme,
    ).copyWith(
      bodyLarge:  const TextStyle(color: textPrimary),
      bodyMedium: const TextStyle(color: textPrimary),
      bodySmall:  const TextStyle(color: textSecond),
    ),
    cardTheme: CardThemeData(
      color: surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: border, width: 0.5),
      ),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: background,
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}