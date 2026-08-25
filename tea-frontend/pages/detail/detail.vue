<template>
	<view class="page" v-if="tea">
		<!-- 茶品信息卡片 -->
		<view class="info-card">
			<text class="name">{{ tea.nameZh }}</text>
			<text class="en-name">{{ tea.nameEn || '' }}</text>
			<view class="meta-row">
				<text class="tag">{{ tea.category }}</text>
				<text class="meta-text">{{ tea.origin || '产地未知' }}</text>
			</view>
			<text v-if="tea.process" class="process">{{ tea.process }}</text>
			<text v-if="tea.flavor" class="flavor">风味：{{ tea.flavor }}</text>
		</view>

		<!-- 成分可视化（条形图，无第三方依赖） -->
		<view class="section" v-if="compositions.length > 0">
			<text class="section-title">成分构成</text>
			<view class="comp-list">
				<view v-for="(c, idx) in compositions" :key="c.id || idx" class="comp-item">
					<text class="comp-name">{{ c.name }}</text>
					<view class="comp-bar-bg">
						<view class="comp-bar" :style="{ width: barWidth(c.value) }"></view>
					</view>
					<text class="comp-value">{{ c.value }}{{ c.unit || '' }}</text>
				</view>
			</view>
		</view>

		<!-- 风味词 -->
		<view class="section" v-if="flavors.length > 0">
			<text class="section-title">风味词汇</text>
			<view class="flavor-tags">
				<text v-for="(f, idx) in flavors" :key="f.id || idx" class="flavor-tag">
					{{ f.termZh || f.termEn || '' }}
				</text>
			</view>
		</view>
	</view>
	<view v-else class="loading">加载中...</view>
</template>

<script>
import { getTeaDetail } from '../../common/api.js'

export default {
	data() {
		return {
			tea: null,
			compositions: [],
			flavors: [],
			maxComp: 1
		}
	},
	onLoad(options) {
		const id = options.id
		if (id) {
			this.loadDetail(id)
		}
	},
	methods: {
		async loadDetail(id) {
			try {
				const detail = await getTeaDetail(id)
				this.tea = detail.tea
				this.compositions = detail.compositions || []
				this.flavors = detail.flavors || []
				// 找最大值用于条形图宽度归一化
				this.maxComp = Math.max(...this.compositions.map(c => c.value || 0), 1)
			} catch (e) {
				console.error('加载详情失败', e)
				uni.showToast({ title: '加载失败', icon: 'none' })
			}
		},
		barWidth(value) {
			// 归一化到 0-100%
			const ratio = (value || 0) / this.maxComp
			return Math.max(ratio * 100, 3) + '%'
		}
	}
}
</script>

<style scoped>
.page {
	padding: 20rpx;
}

.info-card {
	padding: 30rpx;
	border-radius: 16rpx;
	background: linear-gradient(135deg, #1a6b4a, #2e8b57);
	margin-bottom: 20rpx;
}

.name {
	display: block;
	font-size: 56rpx;
	font-weight: bold;
	color: #ffffff;
}

.en-name {
	display: block;
	margin-top: 8rpx;
	font-size: 30rpx;
	color: rgba(255, 255, 255, 0.7);
}

.meta-row {
	display: flex;
	align-items: center;
	margin-top: 20rpx;
	gap: 16rpx;
}

.tag {
	padding: 8rpx 24rpx;
	border-radius: 24rpx;
	font-size: 28rpx;
	color: #1a6b4a;
	background: #ffffff;
}

.meta-text {
	font-size: 30rpx;
	color: rgba(255, 255, 255, 0.85);
}

.process,
.flavor {
	display: block;
	margin-top: 18rpx;
	font-size: 30rpx;
	line-height: 1.6;
	color: rgba(255, 255, 255, 0.85);
}

.section {
	padding: 30rpx;
	border-radius: 16rpx;
	background: #ffffff;
	margin-bottom: 20rpx;
}

.section-title {
	display: block;
	font-size: 36rpx;
	font-weight: bold;
	color: #2c2c2c;
	margin-bottom: 24rpx;
}

.comp-item {
	display: flex;
	align-items: center;
	margin-bottom: 20rpx;
}

.comp-name {
	width: 160rpx;
	font-size: 30rpx;
	color: #2c2c2c;
	flex-shrink: 0;
}

.comp-bar-bg {
	flex: 1;
	height: 24rpx;
	border-radius: 12rpx;
	background: #f0f0f0;
	overflow: hidden;
}

.comp-bar {
	height: 100%;
	border-radius: 12rpx;
	background: linear-gradient(90deg, #2e8b57, #1a6b4a);
}

.comp-value {
	width: 140rpx;
	text-align: right;
	font-size: 28rpx;
	color: #6b6b6b;
	flex-shrink: 0;
}

.flavor-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
}

.flavor-tag {
	padding: 12rpx 28rpx;
	border-radius: 32rpx;
	font-size: 30rpx;
	color: #1a6b4a;
	background: #e8f3ee;
}

.loading {
	padding: 100rpx 0;
	text-align: center;
	color: #9a9a9a;
}
</style>
