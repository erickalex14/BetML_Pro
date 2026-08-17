import 'package:flutter/foundation.dart';
import '../../domain/entities/parlay.dart';

class CouponSelection {
  final ParlaySeleccionInput input;
  final String partido;
  final String liga;
  final String mercado;
  final double probabilidad;

  const CouponSelection({
    required this.input,
    required this.partido,
    required this.liga,
    required this.mercado,
    required this.probabilidad,
  });
}

class PredictionCouponProvider extends ChangeNotifier {
  static const maxSelections = 30;
  final Map<int, CouponSelection> _items = {};

  List<CouponSelection> get items => List.unmodifiable(_items.values);
  int get count => _items.length;
  bool get isEmpty => _items.isEmpty;
  CouponSelection? forMatch(int partidoId) => _items[partidoId];

  void toggle(CouponSelection item) {
    final id = item.input.partidoId;
    if (_items[id]?.input.mercado == item.input.mercado) {
      _items.remove(id);
    } else if (_items.containsKey(id) || _items.length < maxSelections) {
      _items[id] = item;
    }
    notifyListeners();
  }

  void remove(int partidoId) {
    if (_items.remove(partidoId) != null) notifyListeners();
  }

  void clear() {
    if (_items.isEmpty) return;
    _items.clear();
    notifyListeners();
  }
}
