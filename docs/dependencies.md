# Dependencies

## 概要

cow-labelImgの動作に必要な外部ライブラリと依存関係の詳細です。

## Python要件

### Pythonバージョン
- Python 3.6以上
- 推奨: Python 3.8 - 3.10

## 必須パッケージ

### GUI Framework
```
PyQt5>=5.15.0
- QtCore: コアクラスとシグナル/スロット
- QtGui: 描画とイベント処理
- QtWidgets: UIウィジェット
```

### 画像処理
```
Pillow>=8.0.0
- 画像読み込み/保存
- フォーマット変換
- サイズ取得
```

### 数値計算
```
numpy>=1.19.0
- 配列操作
- IOU計算 (labelImg.py:2312-2336)
- 座標変換
```

### 最適化アルゴリズム
```
scipy>=1.5.0
- linear_sum_assignment: ハンガリアンアルゴリズム (libs/tracker.py)
- 形状マッチング最適化
```

### XML処理
```
lxml>=4.6.0
- Pascal VOC形式のXML読み書き (libs/pascal_voc_io.py)
- 高速なXMLパース
```

## オプションパッケージ

### 開発ツール
```
pytest>=6.0.0      # テスト実行
black>=20.8b1      # コードフォーマット
flake8>=3.8.0      # リンター
mypy>=0.800        # 型チェック
```

### デバッグツール
```
ipdb>=0.13.0       # デバッガー
memory_profiler    # メモリプロファイリング
line_profiler      # ラインプロファイリング
```

## インストール方法

### pip使用
```bash
pip install -r requirements.txt
```

### conda使用
```bash
conda install pyqt numpy scipy pillow lxml
```

### 個別インストール
```bash
pip install PyQt5>=5.15.0
pip install numpy>=1.19.0
pip install scipy>=1.5.0
pip install Pillow>=8.0.0
pip install lxml>=4.6.0
```

## requirements.txt
```
PyQt5>=5.15.0
numpy>=1.19.0
scipy>=1.5.0
Pillow>=8.0.0
lxml>=4.6.0
```

## 依存関係の詳細

### PyQt5
- **用途**: GUI全般
- **重要クラス**:
  - QMainWindow: メインウィンドウ (labelImg.py:80)
  - QDialog: ダイアログ (libs/quick_id_selector.py:8)
  - QWidget: ウィジェット基底
  - QPainter: 描画処理 (libs/canvas.py)
  - QAction: アクション定義 (labelImg.py:400-600)

### numpy
- **用途**: 数値計算
- **使用箇所**:
  - IOU計算 (labelImg.py:2312-2336)
  - 座標配列操作
  - 行列演算

### scipy
- **用途**: 最適化アルゴリズム
- **使用箇所**:
  - ハンガリアンアルゴリズム（形状マッチング） (libs/tracker.py:35-50)
  - コスト行列計算

### Pillow
- **用途**: 画像処理
- **使用箇所**:
  - 画像サイズ取得 (labelImg.py:2920-2935)
  - フォーマット変換
  - サムネイル生成

### lxml
- **用途**: XML処理
- **使用箇所**:
  - Pascal VOC形式の読み書き (libs/pascal_voc_io.py)
  - XMLバリデーション

## バージョン互換性

### PyQt5
- 5.15.x: 完全互換
- 5.14.x: 互換（一部機能制限）
- 5.13.x以下: 非推奨

### Python
- 3.10: 完全互換
- 3.9: 完全互換
- 3.8: 完全互換
- 3.7: 互換
- 3.6: 最小要件
- 3.5以下: 非対応

## プラットフォーム別注意事項

### Windows
- PyQt5のインストールに Visual C++ 再頒布可能パッケージが必要
- パス区切り文字の処理に注意

### macOS
- PyQt5のインストールにXcode Command Line Toolsが必要
- Retina display対応

### Linux
- システムのQt5ライブラリとの競合に注意
- X11またはWaylandが必要

## トラブルシューティング

### PyQt5インストールエラー
```bash
# pipアップグレード
pip install --upgrade pip

# wheelパッケージインストール
pip install wheel

# PyQt5再インストール
pip install --force-reinstall PyQt5
```

### ImportError対処
```python
# Qt platform plugin エラーの場合
import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/path/to/plugins'
```

### メモリ不足
- 大量の画像処理時はPillowのサムネイル機能を使用
- numpyの配列は明示的に削除

## ライセンス情報

### 各ライブラリのライセンス
- PyQt5: GPL v3 / Commercial
- numpy: BSD 3-Clause
- scipy: BSD 3-Clause
- Pillow: HPND
- lxml: BSD