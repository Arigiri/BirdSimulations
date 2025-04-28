# Checklist sửa lỗi Weather Simulation

## Nguyên nhân chính
- Sử dụng API không tồn tại: `generate_uniform()` không có trong lớp `WindField` của C++ module
- Lỗi "negative dimensions": Có thể do kích thước mảng không khớp hoặc tham số âm

## Phải sửa trong file `dynamic_viz.py`
- [ ] Sửa phương thức `step()`: Đảm bảo dt luôn dương và đủ lớn
  - Ví dụ: `dt = max(0.05, cfl_dt)`
- [ ] Sửa tất cả cuộc gọi `solve_rk4_step()`: Đảm bảo tham số đều hợp lệ (dương)
- [ ] Kiểm tra kích thước của `temp`, `wind_x`, `wind_y` trước khi truyền cho solver
  - Thêm mã kiểm tra: `if temp.size != width * height: print("Kích thước không khớp")`
- [ ] Xử lý ngoại lệ cho các phép tính quan trọng

## Phải sửa trong file `realtime_viz.py`
- [ ] Thay thế tất cả lệnh gọi `generate_uniform()` bằng `generate_gaussian_field()`
  - Sai: `wind_field.generate_uniform(0.5, 0.5)`
  - Đúng: `wind_field.generate_gaussian_field(1, 0.5, width//10)`
- [ ] Sửa phương thức `set_initial_conditions()`: Đảm bảo sử dụng API đúng
- [ ] Sửa phương thức `step()`: Kiểm soát bước thời gian

## Các file khác có thể cần sửa
- [ ] `mp_test.py`: Kiểm tra các cuộc gọi API WindField
- [ ] `simulation_test.py`: Kiểm tra các cuộc gọi API WindField
- [ ] `logic_optimized.py`: Kiểm tra các cuộc gọi API WindField

## Thay đổi trong mọi file
- [ ] Tìm và thay thế: `wind_field.generate_uniform()` -> `wind_field.generate_gaussian_field()`
- [ ] Đảm bảo `dt` luôn dương: `dt = max(0.05, compute_cfl_time_step(...))`
- [ ] Kiểm tra kích thước mảng: `assert temp.size == width * height`

## API chính xác của module C++

```
Solver:
- compute_cfl_time_step(wind_x, wind_y)
- solve_rk4_step(temp, wind_x, wind_y, dt)

WindField:
- generate_gaussian_field(num_vortices, strength, radius)
- get_wind_x()
- get_wind_y()

TemperatureField:
- set_uniform(temperature)
- set_gradient(min_temp, max_temp, direction)
- add_heat_source(x, y, strength, radius)
- get_temperature()
- set_temperature(temperature)
```

## Quy trình kiểm tra
1. Sửa lỗi trong các file
2. Chạy kiểm tra từng file riêng lẻ
3. Chạy `dynamic_viz.py` cuối cùng để xác nhận các sửa đổi đã khắc phục lỗi
