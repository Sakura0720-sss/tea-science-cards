package com.bmcy.tea.repository;

import com.bmcy.tea.entity.Composition;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CompositionRepository extends JpaRepository<Composition, Long> {
    List<Composition> findByTeaProductId(Long teaProductId);
}
