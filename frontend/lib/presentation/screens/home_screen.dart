import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/product_analytics.dart';
import '../../domain/entities/partido.dart';
import '../providers/partidos_provider.dart';
import '../widgets/clay.dart';
import '../widgets/confidence.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/team_logo.dart';
import '../widgets/design_system.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    ProductAnalytics.track('screen_view', {'screen': 'hoy'});
    Future.microtask(() {
      if (mounted) context.read<PartidosProvider>().cargarPartidosHoy();
    });
    // el backend refresca marcador/estado cada 15 min (job_partidos_en_vivo)
    // — 60s alcanza para que se sienta "en vivo" sin bombardear al propio
    // backend con requests que igual van a devolver lo mismo la mayoría
    // de las veces
    _autoRefresh = Timer.periodic(const Duration(seconds: 60), (_) {
      if (mounted) {
        context
            .read<PartidosProvider>()
            .cargarPartidosHoy(mostrarCargando: false);
      }
    });
  }

  @override
  void dispose() {
    _autoRefresh?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: AppHeader(
        title: 'Hoy',
        subtitle: 'Predicciones y contexto del día',
        actions: [
          IconButton(
            icon: Icon(Icons.image_search_rounded, color: c.textSecond),
            tooltip: 'Analizar captura',
            onPressed: () => context.push('/analizar-captura'),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: c.textSecond),
            tooltip: 'Actualizar',
            onPressed: () =>
                context.read<PartidosProvider>().cargarPartidosHoy(),
          ),
        ],
      ),
      body: Consumer<PartidosProvider>(
        builder: (context, provider, _) {
          if (provider.cargando) return _CargandoLista();
          if (provider.error != null) {
            return _Error(
                mensaje: provider.error!, onRetry: provider.cargarPartidosHoy);
          }
          if (provider.partidos.isEmpty) {
            return _Vacio();
          }

          final firmes = provider.partidos
              .where((p) => p.prediccion?.mercados.isNotEmpty == true)
              .toList()
            ..sort((a, b) {
              final pa = a.prediccion!.mercados
                  .map((m) => m.probabilidad)
                  .reduce((x, y) => x > y ? x : y);
              final pb = b.prediccion!.mercados
                  .map((m) => m.probabilidad)
                  .reduce((x, y) => x > y ? x : y);
              return pb.compareTo(pa);
            });
          final resto = provider.porLiga;

          return ListView(
            padding: const EdgeInsets.only(top: 4, bottom: 16),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
                child: SectionHeading(
                  'Radar del día',
                  subtitle:
                      '${provider.partidos.length} partidos · ${provider.fecha}',
                  trailing: TextButton.icon(
                    onPressed: () => context.go('/oportunidades'),
                    icon: const Icon(Icons.radar_rounded, size: 17),
                    label: const Text('Ver valor'),
                  ),
                ),
              ),
              if (firmes.isNotEmpty) ...[
                _FirmesCarousel(partidos: firmes.take(6).toList()),
                const SizedBox(height: 16),
              ],
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 2, 16, 10),
                child: SectionHeading('Agenda',
                    subtitle: 'Horarios en tu zona local'),
              ),
              _LigaFilter(provider: provider),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  children: resto.map((p) => _LedgerRow(partido: p)).toList(),
                ),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/parlay'),
        icon: const Icon(Icons.add_circle_outline_rounded),
        label: const Text('Crear parlay'),
      ),
      bottomNavigationBar: const AppBottomNav(current: AppTab.hoy),
    );
  }
}

class _FirmesCarousel extends StatelessWidget {
  final List<Partido> partidos;
  const _FirmesCarousel({required this.partidos});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 154,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        scrollDirection: Axis.horizontal,
        itemCount: partidos.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (_, i) => _FirmeCard(partido: partidos[i]),
      ),
    );
  }
}

class _FirmeCard extends StatelessWidget {
  final Partido partido;
  const _FirmeCard({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final mercados = [...partido.prediccion!.mercados]
      ..sort((a, b) => b.probabilidad.compareTo(a.probabilidad));
    final mercado = mercados.first;
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: () => showModalBottomSheet(
        context: context,
        showDragHandle: true,
        builder: (_) => Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
          child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${partido.local} — ${partido.visitante}',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 10),
                Text(mercado.label,
                    style:
                        TextStyle(color: c.pitch, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Text(
                    'Es una de las probabilidades más altas calculadas hoy. Revisa cuotas, contexto y alineaciones antes de guardarla; probabilidad no significa certeza.',
                    style: TextStyle(color: c.textSecond, height: 1.4)),
                const SizedBox(height: 16),
                SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/partido/${partido.id}');
                      },
                      child: const Text('Ver análisis completo'),
                    )),
              ]),
        ),
      ),
      child: Container(
        width: 245,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: c.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: c.lineStrong),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            TeamLogo(url: partido.localLogo, nombre: partido.local, size: 28),
            const SizedBox(width: 5),
            TeamLogo(
                url: partido.visitanteLogo,
                nombre: partido.visitante,
                size: 28),
            const Spacer(),
            Text('${(mercado.probabilidad * 100).toStringAsFixed(0)}%',
                style: AppTheme.score(c, size: 18).copyWith(color: c.pitch)),
          ]),
          const SizedBox(height: 9),
          Text('${partido.local} — ${partido.visitante}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: c.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 5),
          Text(mercado.label,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style:
                  TextStyle(color: c.textSecond, fontSize: 12, height: 1.25)),
          const Spacer(),
          Text('Toca para ver la explicación',
              style: TextStyle(
                  color: c.ledger, fontSize: 11, fontWeight: FontWeight.w600)),
        ]),
      ),
    );
  }
}

// Conservada para una futura variante A/B de tarjeta grande.
// ignore: unused_element
class _FeaturedCard extends StatelessWidget {
  final Partido partido;
  const _FeaturedCard({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion!;
    return ClayContainer(
      padding: const EdgeInsets.fromLTRB(17, 16, 17, 15),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
                color: c.ledgerSoft, borderRadius: BorderRadius.circular(5)),
            child: Text('OPORTUNIDAD DESTACADA',
                style: AppTheme.eyebrow(c, color: c.ledger)),
          ),
          Text(partido.liga,
              style: TextStyle(color: c.textSecond, fontSize: 11.5)),
        ]),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(
            child: Column(children: [
              TeamLogo(url: partido.localLogo, nombre: partido.local, size: 32),
              const SizedBox(height: 6),
              Text(partido.local,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  style: TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                      color: c.text)),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Column(children: [
              Text(partido.hora, style: AppTheme.score(c, size: 15)),
              Text('hoy', style: TextStyle(fontSize: 10, color: c.textSecond)),
            ]),
          ),
          Expanded(
            child: Column(children: [
              TeamLogo(
                  url: partido.visitanteLogo,
                  nombre: partido.visitante,
                  size: 32),
              const SizedBox(height: 6),
              Text(partido.visitante,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  style: TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                      color: c.text)),
            ]),
          ),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          _prob('LOCAL', pred.probLocal, pred.resultado == 'Local', c),
          const SizedBox(width: 8),
          _prob('EMPATE', pred.probEmpate, pred.resultado == 'Empate', c),
          const SizedBox(width: 8),
          _prob('VISITA', pred.probVisitante, pred.resultado == 'Visitante', c),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          Text('Confianza',
              style: TextStyle(fontSize: 11, color: c.textSecond)),
          const SizedBox(width: 10),
          Expanded(child: ConfidenceMeter(value: pred.confianza)),
        ]),
        const SizedBox(height: 13),
        ClayButton(
            label: 'Entender la predicción',
            icon: Icons.analytics_outlined,
            onPressed: () {
              ProductAnalytics.track('detail_opened', {'source': 'hoy'});
              context.push('/partido/${partido.id}');
            }),
      ]),
    );
  }

  Widget _prob(String label, double prob, bool hi, AppColors c) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
            color: hi ? c.pitch : c.bg2,
            borderRadius: BorderRadius.circular(12)),
        child: Column(children: [
          Text('${(prob * 100).toStringAsFixed(0)}%',
              style: AppTheme.score(c, size: 16)
                  .copyWith(color: hi ? c.bg : c.text)),
          const SizedBox(height: 1),
          Text(label,
              style: TextStyle(
                  fontSize: 9.5,
                  color: hi ? c.bg.withValues(alpha: 0.75) : c.textSecond)),
        ]),
      ),
    );
  }
}

class _LigaFilter extends StatelessWidget {
  final PartidosProvider provider;
  const _LigaFilter({required this.provider});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      height: 34,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _Chip(
              label: 'Todas',
              selected: provider.ligaFiltro == null,
              onTap: () {
                ProductAnalytics.track(
                    'filter_applied', {'type': 'liga', 'value': 'todas'});
                provider.setFiltroLiga(null);
              },
              c: c),
          ...provider.ligasDisponibles.map((liga) => _Chip(
                label: liga,
                selected: provider.ligaFiltro == liga,
                onTap: () {
                  ProductAnalytics.track('filter_applied', {'type': 'liga'});
                  provider.setFiltroLiga(liga);
                },
                c: c,
              )),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final AppColors c;
  const _Chip(
      {required this.label,
      required this.selected,
      required this.onTap,
      required this.c});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 13),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected ? c.pitch : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border:
              Border.all(color: selected ? c.pitch : c.lineStrong, width: 0.7),
        ),
        child: Text(label,
            style: TextStyle(
                color: selected ? c.bg : c.textSecond,
                fontSize: 12,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal)),
      ),
    );
  }
}

// Fila ledger — regla horizontal, no card repetida. La barra lateral
// marca si el pick es fuerte (pitch) o no hay predicción (línea).
class _LedgerRow extends StatelessWidget {
  final Partido partido;
  const _LedgerRow({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion;
    final fuerte = pred != null && pred.altaConfianza;

    return InkWell(
      onTap: () => context.push('/partido/${partido.id}'),
      child: Container(
        decoration:
            BoxDecoration(border: Border(bottom: BorderSide(color: c.line))),
        padding: const EdgeInsets.symmetric(vertical: 11),
        child: Row(children: [
          Container(
              width: 3,
              height: 30,
              decoration: BoxDecoration(
                  color: fuerte ? c.pitch : c.lineStrong,
                  borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: 11),
          SizedBox(
            width: 44,
            child: Stack(children: [
              TeamLogo(url: partido.localLogo, nombre: partido.local, size: 22),
              Positioned(
                left: 14,
                child: Container(
                  padding: const EdgeInsets.all(1.5),
                  decoration:
                      BoxDecoration(color: c.bg, shape: BoxShape.circle),
                  child: TeamLogo(
                      url: partido.visitanteLogo,
                      nombre: partido.visitante,
                      size: 22),
                ),
              ),
            ]),
          ),
          const SizedBox(width: 8),
          Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(partido.liga.toUpperCase(), style: AppTheme.eyebrow(c)),
              const SizedBox(height: 3),
              Text('${partido.local} — ${partido.visitante}',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w500,
                      color: c.text)),
            ]),
          ),
          const SizedBox(width: 8),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Text(partido.marcador,
                style: AppTheme.score(c, size: 12, weight: FontWeight.w500)
                    .copyWith(color: c.textSecond)),
            if (partido.enJuego) ...[
              const SizedBox(height: 2),
              Row(mainAxisSize: MainAxisSize.min, children: [
                Container(
                    width: 5,
                    height: 5,
                    decoration:
                        BoxDecoration(color: c.brick, shape: BoxShape.circle)),
                const SizedBox(width: 3),
                Text(partido.minutoTexto,
                    style: TextStyle(
                        fontSize: 9.5,
                        color: c.brick,
                        fontWeight: FontWeight.w600)),
              ]),
            ],
          ]),
          const SizedBox(width: 10),
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: fuerte ? c.pitchSoft : c.bg2,
              borderRadius: BorderRadius.circular(9),
            ),
            alignment: Alignment.center,
            child: Text(
              pred != null ? pred.resultado[0] : '-',
              style: AppTheme.score(c, size: 12)
                  .copyWith(color: fuerte ? c.pitch : c.textSecond),
            ),
          ),
        ]),
      ),
    );
  }
}

class _CargandoLista extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      itemBuilder: (_, __) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(children: [
          _Shimmer(c, width: 34, height: 34, radius: 10),
          const SizedBox(width: 12),
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                _Shimmer(c, width: 120, height: 10),
                const SizedBox(height: 8),
                _Shimmer(c, width: 70, height: 10),
              ])),
        ]),
      ),
    );
  }
}

class _Shimmer extends StatelessWidget {
  final AppColors c;
  final double width, height;
  final double radius;
  const _Shimmer(this.c,
      {required this.width, required this.height, this.radius = 4});

  @override
  Widget build(BuildContext context) {
    return Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
            color: c.bg2, borderRadius: BorderRadius.circular(radius)));
  }
}

class _Vacio extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.event_busy_outlined, size: 40, color: c.textMuted),
          const SizedBox(height: 14),
          Text('Sin partidos hoy',
              style: TextStyle(
                  fontSize: 14, fontWeight: FontWeight.w600, color: c.text)),
          const SizedBox(height: 5),
          Text(
              'El proceso se ejecuta a las 23:55.\nVuelve a revisar más tarde.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12.5, color: c.textSecond)),
        ]),
      ),
    );
  }
}

class _Error extends StatelessWidget {
  final String mensaje;
  final VoidCallback onRetry;
  const _Error({required this.mensaje, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
              color: c.brickSoft, borderRadius: BorderRadius.circular(12)),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.error_outline_rounded, color: c.brick, size: 22),
            const SizedBox(height: 8),
            Text('No pudimos conectar',
                style: TextStyle(
                    fontWeight: FontWeight.w600, color: c.brick, fontSize: 13)),
            const SizedBox(height: 4),
            Text(mensaje,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: c.textSecond)),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: onRetry,
              style: OutlinedButton.styleFrom(
                  foregroundColor: c.brick, side: BorderSide(color: c.brick)),
              child: const Text('Reintentar'),
            ),
          ]),
        ),
      ),
    );
  }
}
