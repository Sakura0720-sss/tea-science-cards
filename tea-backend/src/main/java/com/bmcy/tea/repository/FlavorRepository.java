package com.bmcy.tea.repository;

import com.bmcy.tea.entity.Flavor;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FlavorRepository extends JpaRepository<Flavor, Long> {
    List<Flavor> findByTeaProductId(Long teaProductId);
}
