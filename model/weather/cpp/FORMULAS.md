# Công Thức Sử Dụng Trong Mô Hình Nhiệt Độ Torus

## 1. Đạo hàm riêng bậc nhất (Gradient)

Cho trường nhiệt độ rời rạc $T_{i,j}$ trên lưới kích thước $W \times H$ với biên tuần hoàn:

- **Đạo hàm theo $x$:**

$$
\left(\frac{\partial T}{\partial x}\right)_{i,j} = \frac{T_{i+1,j} - T_{i-1,j}}{2\Delta x}
$$

- **Đạo hàm theo $y$:**

$$
\left(\frac{\partial T}{\partial y}\right)_{i,j} = \frac{T_{i,j+1} - T_{i,j-1}}{2\Delta x}
$$

Với chỉ số $i+1, i-1, j+1, j-1$ được lấy theo modulo kích thước lưới (tức là $i+1 = (i+1) \% W$, $i-1 = (i-1+W) \% W$, tương tự cho $j$).

---

## 2. Toán tử Laplacian (Khuếch tán)

Laplacian rời rạc:

$$
\nabla^2 T_{i,j} = \frac{T_{i+1,j} + T_{i-1,j} + T_{i,j+1} + T_{i,j-1} - 4T_{i,j}}{(\Delta x)^2}
$$

---

## 3. Phương trình đối lưu-khuếch tán (Advection-Diffusion)

Phương trình tổng quát:

$$
\frac{\partial T}{\partial t} = -u \frac{\partial T}{\partial x} - v \frac{\partial T}{\partial y} + \kappa \nabla^2 T
$$

Trong đó:
- $T$: nhiệt độ tại mỗi điểm lưới
- $u, v$: vận tốc gió tại mỗi điểm
- $\kappa$: hệ số khuếch tán nhiệt
- $\Delta x$: bước lưới không gian

---

## 4. Điều kiện biên tuần hoàn (Torus)

Mọi phép truy cập $T_{i,j}$ với $i$ hoặc $j$ vượt ngoài phạm vi $[0, W-1]$ hoặc $[0, H-1]$ đều được wrap về phía đối diện:

$$
T_{i,j} = T_{(i+W)\%W,\ (j+H)\%H}
$$

---

## 5. Điều kiện CFL cho bước thời gian

Để đảm bảo ổn định số:

$$
\Delta t \leq \min\left(\frac{0.8\Delta x}{\max |\vec{u}|},\ \frac{0.8\Delta x^2}{2\kappa}\right)
$$

---

## 6. Thuật toán Runge-Kutta bậc 4 (RK4)

Được sử dụng để tích phân phương trình vi phân theo thời gian, đảm bảo độ chính xác cao.

---

**Mọi công thức đều đã được hiện thực trong mã nguồn với biên tuần hoàn cho mô hình torus.**
