import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// "Ledger de cancha" — verde de pitch + papel/tinta cálido + ámbar de
// valor (cuotas, confianza, stake). Paleta deliberadamente corta: 3
// colores con función (pitch=primario/positivo, ledger=valor, brick=
// negativo) + 2 neutros cálidos (ink/paper), no un ramp genérico.
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
    required this.bg, required this.bg2, required this.bg3,
    required this.surface, required this.surfaceClay,
    required this.text, required this.textSecond, required this.textMuted,
    required this.line, required this.lineStrong,
    required this.pitch, required this.pitchSoft,
    required this.ledger, required this.ledgerSoft,
    required this.brick, required this.brickSoft,
    required this.shadowDark, required this.shadowLight,
  });

  // Requerido por ThemeExtension — nunca se anima entre claro/oscuro acá
  // (MaterialApp cambia de theme entero, no interpola), así que alcanza
  // con devolver `this`/`other` en los extremos.
  @override
  AppColors copyWith() => this;

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) =>
      t < 0.5 ? this : (other as AppColors? ?? this);

  // Paleta derivada del logo real (corredor + barras + punto ascendente
  // lima) — no inventada. "pitch" pasa a ser el azul de marca, "ledger"
  // (valor: cuotas/confianza/stake) es el mismo verde lima del punto
  // ascendente del isotipo, no un ámbar elegido a ojo.
  static const dark = AppColors(
    bg: Color(0xFF0A1020), bg2: Color(0xFF121A33), bg3: Color(0xFF1A2440),
    surface: Color(0xFF0F1730), surfaceClay: Color(0xFF141D3A),
    text: Color(0xFFE8ECF7), textSecond: Color(0xFF97A0BD), textMuted: Color(0xFF636D8F),
    line: Color(0xFF232E52), lineStrong: Color(0xFF303D68),
    pitch: Color(0xFF3D74EE), pitchSoft: Color(0xFF16244A),
    ledger: Color(0xFF8CD121), ledgerSoft: Color(0xFF1E2A12),
    brick: Color(0xFFD9695E), brickSoft: Color(0xFF2E1815),
    shadowDark: Color(0x8C000000), shadowLight: Color(0x08FFFFFF),
  );

  static const light = AppColors(
    bg: Color(0xFFF4F6FB), bg2: Color(0xFFE7EBF6), bg3: Color(0xFFD8DEED),
    surface: Color(0xFFFFFFFF), surfaceClay: Color(0xFFFCFDFF),
    text: Color(0xFF10162B), textSecond: Color(0xFF565F80), textMuted: Color(0xFF8791AD),
    line: Color(0xFFDEE3F0), lineStrong: Color(0xFFC7CEE3),
    pitch: Color(0xFF1E5FE0), pitchSoft: Color(0xFFE4ECFD),
    ledger: Color(0xFF5F9A16), ledgerSoft: Color(0xFFE9F5D9),
    brick: Color(0xFFB8483C), brickSoft: Color(0xFFFAE6E3),
    shadowDark: Color(0x29101830), shadowLight: Color(0x99FFFFFF),
  );
}

// Dual-shadow claymorphism — reservado a 2 usos por pantalla como mucho
// (card destacada, nav inferior, CTA principal). Si todo tiene esta
// sombra deja de leerse como acento.
List<BoxShadow> clayShadow(AppColors c, {double strength = 1}) => [
      BoxShadow(color: c.shadowDark, blurRadius: 14 * strength, offset: Offset(6 * strength, 6 * strength)),
      BoxShadow(color: c.shadowLight, blurRadius: 12 * strength, offset: Offset(-5 * strength, -5 * strength)),
    ];

class AppTheme {
  static TextTheme _textTheme(AppColors c) => GoogleFonts.interTextTheme().copyWith(
        bodyLarge: TextStyle(color: c.text),
        bodyMedium: TextStyle(color: c.text),
        bodySmall: TextStyle(color: c.textSecond),
      );

  // Marcador, cuotas, %, stake — mono con cifras tabulares, nunca el
  // mismo sans que el resto de la UI. Es lo que le da identidad al dato.
  static TextStyle score(AppColors c, {double size = 15, FontWeight weight = FontWeight.w700}) =>
      GoogleFonts.jetBrainsMono(color: c.text, fontSize: size, fontWeight: weight, fontFeatures: const [FontFeature.tabularFigures()]);

  static TextStyle eyebrow(AppColors c, {Color? color}) => GoogleFonts.jetBrainsMono(
        color: color ?? c.textMuted, fontSize: 10.5, fontWeight: FontWeight.w600, letterSpacing: 1.1,
      );

  static ThemeData _build(AppColors c, Brightness brightness) => ThemeData(
        brightness: brightness,
        scaffoldBackgroundColor: c.bg,
        primaryColor: c.pitch,
        colorScheme: brightness == Brightness.dark
            ? ColorScheme.dark(primary: c.pitch, secondary: c.ledger, surface: c.surface, error: c.brick)
            : ColorScheme.light(primary: c.pitch, secondary: c.ledger, surface: c.surface, error: c.brick),
        textTheme: _textTheme(c),
        cardTheme: CardThemeData(
          color: c.surface,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: c.line, width: 0.5)),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: c.bg,
          elevation: 0,
          titleTextStyle: TextStyle(color: c.text, fontSize: 17, fontWeight: FontWeight.w600),
        ),
        inputDecorationTheme: InputDecorationTheme(
          labelStyle: TextStyle(color: c.textSecond),
          enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: c.line)),
          focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: c.pitch, width: 1.5)),
        ),
        extensions: [c],
      );

  static ThemeData get darkTheme => _build(AppColors.dark, Brightness.dark);
  static ThemeData get lightTheme => _build(AppColors.light, Brightness.light);
}

// Acceso a los tokens de color desde cualquier BuildContext:
// AppTheme.of(context).pitch — respeta el theme activo (claro u oscuro),
// a diferencia de las AppTheme.primary estáticas que tenía la v1.
extension AppColorsX on BuildContext {
  AppColors get colors => Theme.of(this).extension<AppColors>() ?? AppColors.dark;
}
