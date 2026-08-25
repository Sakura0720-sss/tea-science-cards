package com.bmcy.tea.entity;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * 硬件/流水线上报的数据点。
 * 统一接收层：设备和自动化流水线都往这一张表灌，用 deviceType 区分来源。
 */
@Entity
@Table(name = "device_data", indexes = {
    @Index(name = "idx_device_time", columnList = "deviceId,reportedAt")
})
public class DeviceData {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 设备/产线标识 */
    private String deviceId;

    /** 数据来源类型：hardware / pipeline */
    private String deviceType;

    /** 指标名，如 temperature / humidity / 茶多酚含量 */
    private String metric;

    /** 数值 */
    private Double value;

    /** 单位 */
    private String unit;

    /** 上报时间戳（epoch 毫秒） */
    private Long reportedAt;

    public DeviceData() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getDeviceId() { return deviceId; }
    public void setDeviceId(String deviceId) { this.deviceId = deviceId; }
    public String getDeviceType() { return deviceType; }
    public void setDeviceType(String deviceType) { this.deviceType = deviceType; }
    public String getMetric() { return metric; }
    public void setMetric(String metric) { this.metric = metric; }
    public Double getValue() { return value; }
    public void setValue(Double value) { this.value = value; }
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    public Long getReportedAt() { return reportedAt; }
    public void setReportedAt(Long reportedAt) { this.reportedAt = reportedAt; }
}
