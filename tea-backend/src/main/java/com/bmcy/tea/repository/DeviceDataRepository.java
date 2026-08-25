package com.bmcy.tea.repository;

import com.bmcy.tea.entity.DeviceData;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DeviceDataRepository extends JpaRepository<DeviceData, Long> {
    List<DeviceData> findByDeviceIdOrderByReportedAtDesc(String deviceId);
}
