import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme.dart';
import '../../core/errors/failures.dart';
import '../../core/http/auth_client.dart';
import '../../domain/entities/analisis_imagen.dart';
import '../../data/datasources/analisis_imagen_remote_ds.dart';
import '../widgets/clay.dart';

class AnalizarCapturaScreen extends StatefulWidget {
  const AnalizarCapturaScreen({super.key});

  @override
  State<AnalizarCapturaScreen> createState() => _AnalizarCapturaScreenState();
}

class _AnalizarCapturaScreenState extends State<AnalizarCapturaScreen> {
  Uint8List? _bytes;
  String? _nombre;
  bool _cargando = false;
  AnalisisImagenResultado? _resultado;
  String? _error;

  Future<void> _elegirImagen() async {
    final picker = ImagePicker();
    final archivo =
        await picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
    if (archivo == null) return;
    final bytes = await archivo.readAsBytes();
    setState(() {
      _bytes = bytes;
      _nombre = archivo.name;
      _resultado = null;
      _error = null;
    });
  }

  Future<void> _analizar() async {
    if (_bytes == null) return;
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final ds = AnalisisImagenRemoteDataSource(AuthClient());
      final resultado = await ds.analizar(_bytes!, _nombre ?? 'captura.png');
      setState(() => _resultado = resultado);
    } on Failure catch (f) {
      setState(() => _error = f.mensaje);
    } catch (e) {
      setState(() => _error = 'Sin conexión: $e');
    } finally {
      setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: AppBar(title: const Text('Analizar captura')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text(
            'Subí una captura de un parley/bet builder — leemos equipos y mercados y te decimos qué opina el modelo de cada pata.',
            style: TextStyle(fontSize: 12.5, color: c.textSecond, height: 1.4)),
        const SizedBox(height: 16),
        GestureDetector(
          onTap: _elegirImagen,
          child: Container(
            height: 180,
            decoration: BoxDecoration(
              color: c.bg2,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: c.lineStrong, style: BorderStyle.solid),
            ),
            child: _bytes != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.memory(_bytes!,
                        fit: BoxFit.cover, width: double.infinity))
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        Icon(Icons.add_photo_alternate_outlined,
                            size: 34, color: c.textMuted),
                        const SizedBox(height: 8),
                        Text('Toca para seleccionar una imagen',
                            style:
                                TextStyle(color: c.textSecond, fontSize: 12.5)),
                      ]),
          ),
        ),
        const SizedBox(height: 16),
        ClayButton(
            label: 'Analizar',
            icon: Icons.image_search_rounded,
            loading: _cargando,
            onPressed: _bytes == null ? null : _analizar),
        if (_error != null) ...[
          const SizedBox(height: 14),
          Text(_error!,
              style: TextStyle(color: c.brick, fontSize: 12.5),
              textAlign: TextAlign.center),
        ],
        if (_resultado != null) ...[
          const SizedBox(height: 20),
          _Resultado(resultado: _resultado!),
        ],
      ]),
    );
  }
}

class _Resultado extends StatelessWidget {
  final AnalisisImagenResultado resultado;
  const _Resultado({required this.resultado});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (!resultado.reconocido) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
              color: c.brickSoft, borderRadius: BorderRadius.circular(12)),
          child: Text('No pudimos identificar el partido en la imagen.',
              style: TextStyle(color: c.brick, fontSize: 12.5)),
        ),
        if (resultado.avisos.isNotEmpty) ...[
          const SizedBox(height: 10),
          for (final a in resultado.avisos)
            Text('· $a', style: TextStyle(fontSize: 12, color: c.textSecond)),
        ],
      ]);
    }

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (resultado.avisos.isNotEmpty)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
                color: c.ledgerSoft, borderRadius: BorderRadius.circular(12)),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              for (final a in resultado.avisos)
                Text(a,
                    style:
                        TextStyle(fontSize: 12, color: c.ledger, height: 1.4))
            ]),
          ),
        ),
      if (resultado.probCombinadaEstimada != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: ClayContainer(
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Text('Probabilidad combinada estimada: ',
                  style: TextStyle(fontSize: 12.5, color: c.textSecond)),
              Text(
                  '${(resultado.probCombinadaEstimada! * 100).toStringAsFixed(1)}%',
                  style: AppTheme.score(c, size: 14).copyWith(color: c.pitch)),
            ]),
          ),
        ),
      for (final s in resultado.selecciones) _SeleccionRow(seleccion: s),
      if (resultado.sinReconocer.isNotEmpty) ...[
        const SizedBox(height: 10),
        Text('SIN RECONOCER', style: AppTheme.eyebrow(c)),
        const SizedBox(height: 6),
        for (final linea in resultado.sinReconocer)
          Text(linea, style: TextStyle(fontSize: 11.5, color: c.textMuted)),
      ],
    ]);
  }
}

class _SeleccionRow extends StatelessWidget {
  final SeleccionImagen seleccion;
  const _SeleccionRow({required this.seleccion});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final valueBet = seleccion.recomendacion == 'Value bet';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: seleccion.reconocido ? c.surface : c.bg2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: c.line),
      ),
      child: Row(children: [
        Expanded(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(seleccion.nombreLegible,
                style: TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w500, color: c.text)),
            if (!seleccion.reconocido)
              Text(seleccion.aviso ?? 'No se pudo calcular',
                  style: TextStyle(fontSize: 11.5, color: c.textMuted))
            else if (seleccion.recomendacion != null)
              Text(seleccion.recomendacion!,
                  style: TextStyle(
                      fontSize: 11.5,
                      color: valueBet ? c.pitch : c.textSecond)),
          ]),
        ),
        if (seleccion.probabilidad != null)
          Text('${(seleccion.probabilidad! * 100).toStringAsFixed(0)}%',
              style: AppTheme.score(c, size: 15)
                  .copyWith(color: valueBet ? c.pitch : c.text)),
      ]),
    );
  }
}
