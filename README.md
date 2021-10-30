# Magneto-optical Imaging Tools

## Table of Contents

<!-- vscode-markdown-toc -->

- 1. [Dependencies](#Dependencies)
- 2. [How to setup](#Howtosetup)
  - 2.1. [ローカル環境にセットアップする場合](#)
  - 2.2. [Pipenv を使って仮想環境を構築する場合](#Pipenv)
  - 2.3. [Docker コンテナを作る場合](#Docker)
- 3. [How to use](#Howtouse)
  - 3.1. [`log_folder` の中身](#log_folder)
  - 3.2. [`output_folder` の中身](#output_folder)
- 4. [Other applications](#Otherapplications)
  - 4.1. [Camera view](#Cameraview)
  - 4.2. [Make-GIF](#Make-GIF)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

## 1. <a name='Dependencies'></a>Dependencies

- Python 3.9.4
- NI-VISA
- NI-488.2

## 2. <a name='Howtosetup'></a>How to setup

必要な Python のパッケージと CCD カメラ用のパッケージをインストールする必要がある。

### 2.1. <a name=''></a>ローカル環境にセットアップする場合

```shell
pip install -r requirements.txt
pip install thorlabs_tsi_camera_python_sdk_package.zip
```

### 2.2. <a name='Pipenv'></a>Pipenv を使って仮想環境を構築する場合

```shell
pipenv install
pipenv install thorlabs_tsi_camera_python_sdk_package.zip
```

### 2.3. <a name='Docker'></a>Docker コンテナを作る場合

```shell
docker-compose run --rm -d
```

## 3. <a name='Howtouse'></a>How to use

偏光子の角度依存性を測る際には、測定のセットアップファイルを作成してそれをプログラムに読み込ませる。セットアップファイルの形式は以下のようになっている必要がある。

sequence.yaml

```yaml
material: conbs
output_folder: ./outputs/output
log_folder: ./outputs/log
cn_info:
polarizer:
  angle_start: 0
  angle_end: 10
  step: 10
analyzer:
  angle: 3.15
camera:
  scan_time: 300 # ms
  intensity: 3000 # domain撮影時の画像の平均強度
  roi: [500, 1000, 1000, 1500] # region of interest
capture:
  scan_num: 4
  domain_capture_num: 16
```

このセットアップファイルを使うと、偏光子は `angle_start` から `angle_end` まで、`step` 度間隔で測定を行う。`cn_info` には転移温度以上で測定して得られたクロスニコル状態の情報が入っているフォルダを指定する。このフォルダがない場合には空欄にしておく。

`cn_info` が空の場合にはクロスニコル状態のスキャンから開始する。スキャンではカメラの露光時間は `scan_time` ミリ秒で、`scan_num` 回の積算が行われる。クロスニコル状態の計算で用いられる画像領域は `roi` によって指定する。`roi` の値は下の図のように指定する。

<div style="text-align: center;">
<img src="./assets/roi.svg" width=70%>
</div>

この測定で得られたクロスニコル状態の情報は `log_folder` に保存される。

クロスニコル状態の情報が得られたら、ドメイン観察用の画像撮影が行われる。ドメイン観察では、クロスニコル状態の画像と、検光子がクロスニコル状態から +`angle`, -`angle` だけずらした位置での画像が撮影される。このとき、カメラの露光時間は `roi` 領域での画像の平均強度が `intensity` になるように調整される。また、撮影時の積算回数は `domain_capture_num` 回となる。撮影された画像は `output_folder` に保存される。

測定を開始するには、`src/polar_dep.py` の中身の `config_file` 変数を測定に使うセットアップファイル名に置き換えて実行する。

### 3.1. <a name='log_folder'></a>`log_folder` の中身

クロスニコル情報が YAML 形式で保存される。ファイル名は偏光子の角度が n 度の時 `n_scan_info.yaml` となる。

### 3.2. <a name='output_folder'></a>`output_folder` の中身

撮影された画像が 16bits-TIFF ファイル形式で保存される。偏光子の角度が n のときクロスニコル状態の画像は `cn_n.tif`、クロスニコル状態から+`angle`だけずらしたときの画像は `pos_n.tif`、-`angle` だけずらしたときの画像は `neg_n.tif` となる。

## 4. <a name='Otherapplications'></a>Other applications

### 4.1. <a name='Cameraview'></a>Camera view

カメラの画像のライブビューを表示するアプリケーション。露光時間や偏光子、検光子の角度の調整も可能。実行ファイルは `src/camera_view.py`

### 4.2. <a name='Make-GIF'></a>Make-GIF

画像ファイル群から GIF を生成するアプリケーション。Docker コンテナでの実行を想定している。`src/mkgif/images` 内部に画像を `29k.png` のような名前にして保存しておくと温度が高いときの画像から処理して GIF にしてくれる。

`src/mkgif` ディレクトリで以下のコマンドを実行する。

```shell
docker run --rm -v ${PWD}:/app
```
