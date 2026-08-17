import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Tokens deportivos con semantica fija: azul=estructura, verde=valor,
/// naranja=oportunidad y rojo=riesgo/error.
class AppColors extends ThemeExtension<AppColors> {
  final Color bg, bg2, bg3;
  final Color surface, surfaceClay;
  final Color text, textSecond, textMuted;
  final Color line, lineStrong;
  final Color pitch, pitchSoft;
  final Color ledger, ledgerSoft;
  final Color brick, brickSoft;
  final Color shadowDark, shadowLight;

  const AppColors({
    required this.bg,
    required this.bg2,
    required this.bg3,
    required this.surface,
    required this.surfaceClay,
    required this.text,
    required this.textSecond,
    required this.textMuted,
    required this.line,
    required this.lineStrong,
    required this.pitch,
    required this.pitchSoft,
    required this.ledger,
    required this.ledgerSoft,
    required this.brick,
    required this.brickSoft,
    required this.shadowDark,
    required this.shadowLight,
  });

  @override
  AppColors copyWith() => this;

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) =>
      t < 0.5 ? this : (other as AppColors? ?? this);

  static const dark = AppColors(
    bg: Color(0xFF080D1A),
    bg2: Color(0xFF10182A),
    bg3: Color(0xFF172238),
    surface: Color(0xFF101827),
    surfaceClay: Color(0xFF131D30),
    text: Color(0xFFF4F7FC),
    textSecond: Color(0xFFAAB4C8),
    textMuted: Color(0xFF748098),
    line: Color(0xFF243047),
    lineStrong: Color(0xFF33425E),
    pitch: Color(0xFF4A7DFF),
    pitchSoft: Color(0xFF17264A),
    ledger: Color(0xFF55D68B),
    ledgerSoft: Color(0xFF122D24),
    brick: Color(0xFFFF6B6B),
    brickSoft: Color(0xFF351B22),
    shadowDark: Color(0x52000000),
    shadowLight: Color(0x00000000),
  );

  static const light = AppColors(
    bg: Color(0xFFF4F7FC),
    bg2: Color(0xFFEAF0F8),
    bg3: Color(0xFFDDE6F2),
    surface: Color(0xFFFFFFFF),
    surfaceClay: Color(0xFFFCFDFF),
    text: Color(0xFF10162B),
    textSecond: Color(0xFF565F80),
    textMuted: Color(0xFF8791AD),
    line: Color(0xFFDEE3F0),
    lineStrong: Color(0xFFC7CEE3),
    pitch: Color(0xFF1E5FE0),
    pitchSoft: Color(0xFFE4ECFD),
    ledger: Color(0xFF168A4B),
    ledgerSoft: Color(0xFFE3F7EC),
    brick: Color(0xFFB8483C),
    brickSoft: Color(0xFFFAE6E3),
    shadowDark: Color(0x24101830),
    shadowLight: Color(0x00000000),
  );
}

List<BoxShadow> clayShadow(AppColors c, {double strength = 1}) => [
      BoxShadow(
          color: c.shadowDark,
          blurRadius: 10 * strength,
          offset: Offset(0, 3 * strength)),
    ];

class AppTheme {
  static TextTheme _textTheme(AppColors c) =>
      GoogleFonts.interTextTheme().copyWith(
        headlineSmall: TextStyle(
            color: c.text,
            fontSize: 24,
            fontWeight: FontWeight.w800,
            height: 1.1),
        titleLarge:
            TextStyle(color: c.text, fontSize: 18, fontWeight: FontWeight.w700),
        titleMedium:
            TextStyle(color: c.text, fontSize: 15, fontWeight: FontWeight.w700),
        bodyLarge: TextStyle(color: c.text, fontSize: 15, height: 1.4),
        bodyMedium: TextStyle(color: c.text, fontSize: 13.5, height: 1.4),
        bodySmall: TextStyle(color: c.textSecond, fontSize: 12, height: 1.35),
      );

  static TextStyle score(AppColors c,
          {double size = 15, FontWeight weight = FontWeight.w700}) =>
      GoogleFonts.jetBrainsMono(
          color: c.text,
          fontSize: size,
          fontWeight: weight,
          fontFeatures: const [FontFeature.tabularFigures()]);

  static TextStyle eyebrow(AppColors c, {Color? color}) =>
      GoogleFonts.jetBrainsMono(
        color: color ?? c.textMuted,
        fontSize: 10.5,
        fontWeight: FontWeight.w600,
        letterSpacing: 1.1,
      );

  static ThemeData _build(AppColors c, Brightness brightness) => ThemeData(
        useMaterial3: true,
        brightness: brightness,
        scaffoldBackgroundColor: c.bg,
        primaryColor: c.pitch,
        colorScheme: brightness == Brightness.dark
            ? ColorScheme.dark(
                primary: c.pitch,
                secondary: c.ledger,
                tertiary: const Color(0xFFFFA24C),
                surface: c.surface,
                error: c.brick)
            : ColorScheme.light(
                primary: c.pitch,
                secondary: c.ledger,
                tertiary: const Color(0xFFD96B00),
                surface: c.surface,
                error: c.brick),
        textTheme: _textTheme(c),
        cardTheme: CardThemeData(
            color: c.surface,
            elevation: 0,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: c.line))),
        dividerColor: c.line,
        appBarTheme: AppBarTheme(
            backgroundColor: c.bg,
            elevation: 0,
            centerTitle: false,
            scrolledUnderElevation: 0,
            titleTextStyle: TextStyle(
                color: c.text, fontSize: 18, fontWeight: FontWeight.w700),
            iconTheme: IconThemeData(color: c.textSecond)),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: c.bg2,
          labelStyle: TextStyle(color: c.textSecond),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none),
          enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: c.line)),
          focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: c.pitch, width: 1.5)),
        ),
        navigationBarTheme: NavigationBarThemeData(
          height: 68,
          backgroundColor: c.surface,
          indicatorColor: c.pitchSoft,
          labelTextStyle: WidgetStateProperty.resolveWith((states) => TextStyle(
              color:
                  states.contains(WidgetState.selected) ? c.text : c.textMuted,
              fontSize: 11,
              fontWeight: states.contains(WidgetState.selected)
                  ? FontWeight.w700
                  : FontWeight.w500)),
          iconTheme: WidgetStateProperty.resolveWith((states) => IconThemeData(
              color:
                  states.contains(WidgetState.selected) ? c.pitch : c.textMuted,
              size: 22)),
        ),
        filledButtonTheme: FilledButtonThemeData(
            style: FilledButton.styleFrom(
                minimumSize: const Size(48, 48),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                textStyle: const TextStyle(fontWeight: FontWeight.w700))),
        outlinedButtonTheme: OutlinedButtonThemeData(
            style: OutlinedButton.styleFrom(
                minimumSize: const Size(48, 48),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                side: BorderSide(color: c.lineStrong))),
        extensions: [c],
      );

  static ThemeData get darkTheme => _build(AppColors.dark, Brightness.dark);
  static ThemeData get lightTheme => _build(AppColors.light, Brightness.light);
}

extension AppColorsX on BuildContext {
  AppColors get colors =>
      Theme.of(this).extension<AppColors>() ?? AppColors.dark;
}
