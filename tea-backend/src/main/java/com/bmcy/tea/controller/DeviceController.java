package com.bmcy.tea.controller;

import com.bmcy.tea.entity.DeviceData;
import com.bmcy.tea.repository.DeviceDataRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 统一数据接收层：硬件和自动化流水线都往这里上报。
 * 用 deviceType 区分来源（hardware / pipeline），metric 表示指标名。
 */
@RestController
@RequestMapping("/api/device")
public class DeviceController {

    private final DeviceDataRepository repository;

    public DeviceController(DeviceDataRepository repository) {
        this.repository = repository;
    }

    /** 单条上报 */
    @PostMapping("/report")
    public DeviceData report(@RequestBody DeviceData data) {
        if (data.getReportedAt() == null) {
            data.setReportedAt(System.currentTimeMillis());
        }
        return repository.save(data);
    }

    /** 批量上报（流水线一次吐多条） */
    @PostMapping("/report/batch")
    public List<DeviceData> reportBatch(@RequestBody List<DeviceData> list) {
        list.forEach(d -> {
            if (d.getReportedAt() == null) {
                d.setReportedAt(System.currentTimeMillis());
            }
        });
        return repository.saveAll(list);
    }

    /** 查询某设备的数据 */
    @GetMapping("/{deviceId}")
    public List<DeviceData> query(@PathVariable String deviceId) {
        return repository.findByDeviceIdOrderByReportedAtDesc(deviceId);
    }

    /** 健康检查 */
    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "count", repository.count());
    }
}
