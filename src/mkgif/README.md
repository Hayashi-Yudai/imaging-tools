# mkgif

`images` ディレクトリ下にある画像ファイルからGIFを作成。
画像ファイルの拡張子は`.png`、ファイル名は数字(温度や磁場)のみで較正されていることを想定している。
生成されたGIFはファイル名の数字の降順に画像を加工したものになる

## How to run

Dockerコンテナ内で動作することを想定している

```bash
$ docker build -t make_gif
$ docker run --rm -v ${PWD}:/app/ make_gif:latest
```

## How to change sequence

数字の昇順に並び替えたいときには `make_gif.py` の16行目を

```python
img_list.sort(key=lambda x: -float(x.rsplit("/", 1)[1].rsplit(".", 1)[0]))
```

から

```python
img_list.sort(key=lambda x: float(x.rsplit("/", 1)[1].rsplit(".", 1)[0]))
```

に変更する 
