from PIL import Image, ImageDraw, ImageFont
import math

# ==================== 準備 ====================
# インプット指定
default_size = 1500
user_input1 = input(f"数値を入力してください（デフォルト値{default_size}）: ")
user_input2 = input("画像の上半分と下半分で異なる配色にする場合は1を入力：")

# 新規画像作成
size = int(user_input1) if user_input1 != "" else default_size
width, height, radius = size, size * 2 // 3, size // 6

main_color = (188, 0, 45)
bkg_color = (255, 255, 255)

output = Image.new("RGB", (width, height), bkg_color)
draw = ImageDraw.Draw(output)

# 画像の上半分と下半分で異なる配色にする場合
user_input_val = bool(int(user_input2) if user_input2 != "" else 0)
if user_input_val:
  main_color = (205,0,0) #上半分
  bkg_color1 = (0,86,184) #上半分
  bkg_color2 = (255,216,0) #下半分
  sub_color = (0,0,0) #下半分

#保存したい画像のファイル名とファイル形式の設定
filename = str(f"output_{width}x{height}.png")

# 基線の色と幅の設定
line_color = main_color
line_width = 1

# 外枠の色と幅の設定
frame_color = (0,0,0) #black
frame_line_width = 1

# 角度設定
deg1 = 39.375
deg2 = 28.125
deg3 = 11.5 # 各傾斜線間の角度間隔

# 斜線の設定可能なパラメータ
NUM_LINES_INTER56_TOP = int((180-deg1-deg2)//deg3)
NUM_LINES_INTER67_RIGHT_CW = int(deg2//deg3)
NUM_LINES_INTER67_RIGHT_CCW = int(deg2//deg3)
NUM_LINES_INTER78_BOTTOM = int((180-deg1-deg2)//deg3)
NUM_LINES_INTER85_LEFT_CW = int(deg1//deg3)
NUM_LINES_INTER85_LEFT_CCW = int(deg1//deg3)

# 基線と描画に必要な座標の計算
cx, cy = (0.5 - 1 / 9) * width, height / 2
x1 = 0.5 * height * math.tan(math.radians(90 - deg1))
y1 = height / 2
x2 = width - 0.5 * height * math.tan(math.radians(90 - deg2))
y2 = height / 2
x3 = width * x1 / (x1 + width - x2)
y3 = width * y1 / (x1 + width - x2)
x4 = width * x1 / (x1 + width - x2)
y4 = height + (y1 - height) * width / (x1 + width - x2)
# 基線を描画
draw.line((0, 0, x1, y1), fill=line_color, width=line_width)
draw.line((0, height, x1, y1), fill=line_color, width=line_width)
draw.line((width, 0, x2, y2), fill=line_color, width=line_width)
draw.line((width, height, x2, y2), fill=line_color, width=line_width)

# 交点定義
inter56 = (x3, y3)
inter67 = (x2, y2)
inter78 = (x4, y4)
inter85 = (x1, y1)

# 基線以外の斜線と辺との交点座標格納リスト
all_intersection_points = []

# ==================== 斜線を描画するためのヘルパー関数 ====================
def draw_angled_lines(draw, start_point, num_lines, angle_step_deg, base_angle_rad, direction, target_boundary, color, line_width, image_width, image_height, all_points_list):
    px, py = start_point
    for i in range(1, num_lines + 1):
        offset_deg = i * angle_step_deg
        new_rad = base_angle_rad + (direction * math.radians(offset_deg))

        dx = math.cos(new_rad)
        dy = math.sin(new_rad)

        ix, iy = None, None

        if target_boundary == 'top':
            # 上向きの力（dyは負の値でなければならない）
            if dy > 0: dx, dy = -dx, -dy
            if abs(dy) < 1e-8: continue
            t = (0 - py) / dy
            ix = px + t * dx
            iy = 0.0
            if not (0 <= ix <= image_width): continue

        elif target_boundary == 'right':
            # 右方向への力（dxは正の値でなければならない）
            if dx < 0: dx, dy = -dx, -dy
            if abs(dx) < 1e-8: continue
            t = (image_width - px) / dx
            ix = float(image_width)
            iy = py + t * dy
            if not (0 <= iy <= image_height): continue

        elif target_boundary == 'bottom':
            # 下向きの力（dyは正の値でなければならない）
            if dy < 0: dx, dy = -dx, -dy
            if abs(dy) < 1e-8: continue
            t = (image_height - py) / dy
            ix = px + t * dx
            iy = float(image_height)
            if not (0 <= ix <= image_width): continue

        elif target_boundary == 'left':
            # 左方向への力（dxは負の値でなければならない）
            if dx > 0: dx, dy = -dx, -dy
            if abs(dx) < 1e-8: continue
            t = (0 - px) / dx
            ix = 0.0
            iy = py + t * dy
            if not (0 <= iy <= image_height): continue

        if ix is not None and iy is not None:
            draw.line((px, py, ix, iy), fill=color, width=line_width)
            all_points_list.append((ix, iy)) # 交点を収集する

def sort_points_clockwise(points, width, height):
    # 一意のポイントをフィルタリングする（浮動小数点数の誤差を処理）
    unique_points = []
    for p_new in points:
        is_duplicate = False
        for p_existing in unique_points:
            # 許容誤差が小さい点を重複点とみなす
            if math.isclose(p_new[0], p_existing[0], abs_tol=1e-3) and math.isclose(p_new[1], p_existing[1], abs_tol=1e-3):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(p_new)

    # (0, height/2) から始まる時計回りの順序のカスタムソートキーを定義します。
    def get_sort_key(point):
        x, y = point
        eps = 1e-6 # 浮動小数点比較には小さなイプシロン値を使用します。

        # セグメント0：左端、（0、height/2）から（0、0）まで
        if abs(x) < eps and y <= height / 2.0 + eps and y >= -eps:
            return 0, -y # -y（yの降順）でソート
        # セグメント1：上端、（0,0）から右方向（width,0）まで
        elif abs(y) < eps and x >= -eps and x <= width + eps:
            return 1, x # xの昇順で並べ替える
        # セグメント 2: 右端、(width,0)から(width,height)まで
        elif abs(x - width) < eps and y >= -eps and y <= height + eps:
            return 2, y # yの昇順で並べ替え
        # セグメント3：下端、（width,height）から左方向（0、height）まで
        elif abs(y - height) < eps and x <= width + eps and x >= -eps:
            return 3, -x # -x（xの降順）でソート
        # セグメント4：左端、（0、height）から（0、height/2）まで
        elif abs(x) < eps and y > height / 2.0 - eps and y <= height + eps:
            return 4, -y # -yでソート（yは減少し、高さから高さの半分の方向へ移動）
        else:
            # 境界線上に正確に位置していない点に対するフォールバック処理
            #（ロジックが正しければ発生しないはず）
            return 5, (x, y)

    sorted_points = sorted(unique_points, key=get_sort_key)
    return sorted_points

# ==================== 計算実行 ====================

print("=== 計算結果 ===")

print(f"\n円の中心座標: ({cx:.1f}, {cy:.1f})")

print(f"(x1,y1)=({x1:.2f},{y1:.2f})")
print(f"(x2,y2)=({x2:.2f},{y2:.2f})")
print(f"(x3,y3)=({x3:.2f},{y3:.2f})")
print(f"(x4,y4)=({x4:.2f},{y4:.2f})")


# ===== inter56 → line1  line5基準・時計回り =====
draw_angled_lines(
    draw, inter56, NUM_LINES_INTER56_TOP, deg3,
    math.atan2(y1 - 0, x1 - 0), 1, 'top', line_color, line_width,
    width, height, all_intersection_points
)

# ===== inter67 → line2  line6基準・時計回り ====== 東南東
draw_angled_lines(
    draw, inter67, NUM_LINES_INTER67_RIGHT_CW, deg3,
    math.atan2(y2 - 0, x2 - width), 1, 'right', line_color, line_width,
    width, height, all_intersection_points
)

# ===== inter67 → line2  line7基準・反時計回り ====== 北東
draw_angled_lines(
    draw, inter67, NUM_LINES_INTER67_RIGHT_CCW, deg3,
    math.atan2(y2 - height, x2 - width), -1, 'right', line_color, line_width,
    width, height, all_intersection_points
)


# ===== inter78 → line3  line8基準・反時計回り ===== 北西
draw_angled_lines(
    draw, inter78, NUM_LINES_INTER78_BOTTOM, deg3,
    math.atan2(y1 - height, x1 - 0), -1, 'bottom', line_color, line_width,
    width, height, all_intersection_points
)

# ====== inter85 → line4  line8基準・時計回り ===== 南西
draw_angled_lines(
    draw, inter85, NUM_LINES_INTER85_LEFT_CW, deg3,
    math.atan2(y1 - height, x1 - 0), 1, 'left', line_color, line_width,
    width, height, all_intersection_points
)

# ===== inter85 → line4  line5基準・反時計回り ===== 北西
draw_angled_lines(
    draw, inter85, NUM_LINES_INTER85_LEFT_CCW, deg3,
    math.atan2(y1 - 0, x1 - 0), -1, 'left', line_color, line_width,
    width, height, all_intersection_points
)

# 収集した交点を時計回りに並べ替える
sorted_all_intersection_points = sort_points_clockwise(all_intersection_points, width, height)
all_intersection_points = sorted_all_intersection_points # all_intersection_pointsを上書き

print("\n--- Intersection Points (Clockwise from (0, height/2)) ---")
for idx, (x, y) in enumerate(all_intersection_points):
    print(f"Point {idx + 1}: ({x:.2f}, {y:.2f})")

# 円を描き直して内側を白で塗りつぶす
draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),fill="white", outline=main_color, width=line_width)
# 線画を保存
output.save(f"output_LineDrawing{width}x{height}.png")
# ==================== 結果出力 ====================

# ポリゴンリストを作成
all_polygons = [
    [inter85, all_intersection_points[27], all_intersection_points[0]],
    [inter85, all_intersection_points[0], all_intersection_points[1]],
    [inter85, all_intersection_points[1], all_intersection_points[2]],
    [inter85, all_intersection_points[2], (0,0)],
    [inter56, (0,0), all_intersection_points[3]],
    [inter56, all_intersection_points[3], all_intersection_points[4]],
    [inter56, all_intersection_points[4], all_intersection_points[5]],
    [inter56, all_intersection_points[5], all_intersection_points[6]],
    [inter56, all_intersection_points[6], all_intersection_points[7]],
    [inter56, all_intersection_points[7], all_intersection_points[8]],
    [inter56, all_intersection_points[8], all_intersection_points[9]],
    [inter56, all_intersection_points[9], all_intersection_points[10]],
    [inter56, all_intersection_points[10], all_intersection_points[11]],
    [inter56, all_intersection_points[11], (width,0)],
    [inter67, (width,0), all_intersection_points[12]],
    [inter67, all_intersection_points[12], all_intersection_points[13]],
    [inter67, all_intersection_points[13], all_intersection_points[14]],
    [inter67, all_intersection_points[14], all_intersection_points[15]],
    [inter67, all_intersection_points[15], (width,height)],
    [inter78, (width,height), all_intersection_points[16]],
    [inter78, all_intersection_points[16], all_intersection_points[17]],
    [inter78, all_intersection_points[17], all_intersection_points[18]],
    [inter78, all_intersection_points[18], all_intersection_points[19]],
    [inter78, all_intersection_points[19], all_intersection_points[20]],
    [inter78, all_intersection_points[20], all_intersection_points[21]],
    [inter78, all_intersection_points[21], all_intersection_points[22]],
    [inter78, all_intersection_points[22], all_intersection_points[23]],
    [inter78, all_intersection_points[23], all_intersection_points[24]],
    [inter78, all_intersection_points[24], (0,height)],
    [inter85, (0,height), all_intersection_points[25]],
    [inter85, all_intersection_points[25], all_intersection_points[26]],
    [inter85, all_intersection_points[26], all_intersection_points[27]]
]
# ポリゴンを描画
for i, polygon_coords in enumerate(all_polygons):
    current_main_color = main_color
    current_bkg_color = bkg_color

    if user_input_val:
        is_lower_half = False
        for point in polygon_coords:
            # いずれかの点のy座標がheight/2より大きいかどうかをチェックします。
            if point[1] > height / 2:
                is_lower_half = True
                break

        if is_lower_half:
            current_main_color = sub_color
            current_bkg_color = bkg_color2
        else:
            current_main_color = main_color
            current_bkg_color = bkg_color1

    fill_color = current_main_color if (i + 1) % 2 != 0 else current_bkg_color
    draw.polygon(polygon_coords, fill=fill_color)

# 円を描き直せば内側を塗り潰せる
if user_input_val:
  draw.polygon([inter85, (0,height/2), all_intersection_points[0]], fill=main_color) # 対称軸上のポリゴンを塗り直す
  draw.polygon([inter67, all_intersection_points[13], (width,height/2)], fill=main_color) # 対称軸上のポリゴンを塗り直す
  draw.pieslice((cx - radius, cy - radius, cx + radius, cy + radius),
                start=180, end=360, fill=main_color, outline=main_color,
                width=line_width)
  draw.pieslice((cx - radius, cy - radius, cx + radius, cy + radius),
                start=0, end=180, fill=sub_color, outline=sub_color,
                width=line_width)
  draw.line((0, height / 2, width, height / 2), fill="black", width=line_width) # 対称軸を引き直す
else:
  draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=main_color, outline=main_color,
                width=line_width)


# 外枠の描画
draw.line((0, 0, width - 1, 0), fill=frame_color, width=frame_line_width)
draw.line((0, 0, 0, height - 1), fill=frame_color, width=frame_line_width)
draw.line((0, height - 1, width - 1, height - 1), fill=frame_color, width=frame_line_width)
draw.line((width - 1, 0, width - 1, height - 1), fill=frame_color, width=frame_line_width)

# 上下塗り分けた時は保存するファイル名をリネームする
if user_input_val:
  filename = str(f"RSAISF{width}x{height}.png")
  print("The Rising Sun always illuminates the Sunflower Field. Slava Ukraini!")
  print("🌅🇯🇵🤝🇺🇦🌻")

#出力された画像の保存と表示
output.save(filename)

output
