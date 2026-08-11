import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../providers/auth_provider.dart';
import '../widgets/clay.dart';

// Navy exacto del PNG del logo (muestreado del archivo) — el header usa
// este color fijo, no el azul de marca del theme, para que la imagen se
// funda sin borde visible. Es la única franja de la app que no sigue
// claro/oscuro: es un bloque de marca, como el header de color fijo de
// cualquier producto con isotipo propio.
const Color _logoNavy = Color(0xFF01062B);

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _modoRegistro = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit(AuthProvider auth) async {
    final ok = _modoRegistro
        ? await auth.registro(_emailCtrl.text.trim(), _passCtrl.text)
        : await auth.login(_emailCtrl.text.trim(), _passCtrl.text);
    if (ok && mounted) Navigator.of(context).maybePop();
  }

  InputDecoration _campo(String label, AppColors c) => InputDecoration(
        labelText: label,
        filled: true,
        fillColor: c.bg2,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      );

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      backgroundColor: _logoNavy,
      body: SafeArea(
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
            child: Column(children: [
              Image.asset('assets/logos/logo_wordmark.png', height: 56, fit: BoxFit.contain),
              const SizedBox(height: 10),
              Text(_modoRegistro ? 'Empezá a apostar con datos, no corazonadas' : 'Tu ventaja, calculada antes de apostar',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Color(0xB3E8ECF7), fontSize: 13)),
            ]),
          ),
          Expanded(
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
              decoration: BoxDecoration(
                color: c.bg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
              ),
              child: Consumer<AuthProvider>(
                builder: (context, auth, _) => SingleChildScrollView(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    Text(_modoRegistro ? 'Crear cuenta' : 'Iniciar sesión',
                        style: TextStyle(fontSize: 19, fontWeight: FontWeight.w600, color: c.text)),
                    const SizedBox(height: 4),
                    Text(
                        _modoRegistro ? '¿Ya tenés cuenta?' : '¿No tenés cuenta todavía?',
                        style: TextStyle(fontSize: 12.5, color: c.textSecond)),
                    const SizedBox(height: 22),
                    TextField(
                      controller: _emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      style: TextStyle(color: c.text),
                      decoration: _campo('Email', c),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _passCtrl,
                      obscureText: true,
                      style: TextStyle(color: c.text),
                      decoration: _campo('Contraseña', c),
                    ),
                    if (auth.error != null) ...[
                      const SizedBox(height: 12),
                      Text(auth.error!, style: TextStyle(color: c.brick, fontSize: 12.5), textAlign: TextAlign.center),
                    ],
                    const SizedBox(height: 20),
                    ClayButton(
                      label: _modoRegistro ? 'Crear cuenta' : 'Ingresar',
                      loading: auth.cargando,
                      onPressed: () => _submit(auth),
                    ),
                    const SizedBox(height: 8),
                    Center(
                      child: TextButton(
                        onPressed: () => setState(() => _modoRegistro = !_modoRegistro),
                        child: Text(
                          _modoRegistro ? 'Ya tengo cuenta' : 'Crear una cuenta nueva',
                          style: TextStyle(color: c.pitch, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ),
                  ]),
                ),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}
