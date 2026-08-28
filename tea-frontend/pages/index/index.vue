<template>
	<view class="layout">
		<!-- 一级导航栏 -->
		<view class="sidebar">
			<view class="side-main" :class="{ active: currentTab === 'tea' }" @click="switchTab('tea')">
				<text class="side-main-text">选茶</text>
			</view>
			<view class="side-main" :class="{ active: currentTab === 'ask' }" @click="switchTab('ask')">
				<text class="side-main-text">智能问答</text>
			</view>
		</view>

		<!-- 二级分类栏（选茶的扩展层） -->
		<view class="sub-sidebar" v-if="currentTab === 'tea'">
			<view
				v-for="cat in allCategories"
				:key="cat"
				class="sub-item"
				:class="{ active: activeCategory === cat }"
				@click="jumpToCategory(cat)"
			>
				<text class="sub-text">{{ cat === '全部' ? '回到顶部' : cat }}</text>
			</view>
		</view>

		<!-- 内容区 -->
		<view class="content">
			<!-- 选茶内容 -->
			<template v-if="currentTab === 'tea'">
				<view v-if="loading" class="loading">加载中...</view>
				<view v-else-if="grouped.length === 0" class="empty">暂无茶品数据</view>
				<scroll-view
					v-else
					scroll-y
					class="tea-scroll"
					:scroll-into-view="scrollToId"
					scroll-with-animation
					@scroll="onScroll"
				>
					<view id="top"></view>
					<view
						v-for="(group, gi) in grouped"
						:key="group.category"
						:id="'cat-' + gi"
						class="group"
					>
						<view class="group-title">{{ group.category }}</view>
						<view
							v-for="tea in group.teas"
							:key="tea.id"
							class="tea-card"
							@click="goDetail(tea.id)"
						>
							<view class="tea-card-left">
								<text class="tea-name">{{ tea.nameZh || '未命名' }}</text>
								<text class="tea-origin">{{ tea.origin || '产地未知' }}</text>
							</view>
							<view class="tea-card-right">
								<text class="tea-std">{{ tea.stdNo || '' }}</text>
							</view>
						</view>
					</view>
				</scroll-view>
			</template>

			<!-- 智能问答内容 -->
			<view v-else class="ask-wrap">
				<view class="chat-area" ref="chatArea">
					<view v-for="(msg, idx) in messages" :key="idx" class="msg-row" :class="msg.role">
						<view class="bubble">
							<text class="msg-text">{{ msg.content }}</text>
							<text v-if="msg.sources && msg.sources.length" class="msg-sources">
								参考：{{ msg.sources.join('；') }}
							</text>
						</view>
					</view>
					<view v-if="asking" class="msg-row assistant">
						<view class="bubble"><text class="msg-text">思考中...</text></view>
					</view>
				</view>
				<view class="input-bar">
					<input
						v-model="question"
						class="input"
						placeholder="问一个茶叶相关的问题..."
						confirm-type="send"
						@confirm="send"
					/>
					<button class="send-btn" size="mini" @click="send">发送</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { getTeaList, askQuestion } from '../../common/api.js'

export default {
	data() {
		return {
			currentTab: 'tea',
			allCategories: ['全部', '绿茶', '乌龙茶', '紧压茶', '黑茶', '红茶', '白茶', '茶制品', '黄茶', '花茶', '茶饮料', '袋泡茶', '抹茶', '基础标准', '其他'],
			activeCategory: '全部',
			teaList: [],
			loading: false,
			scrollToId: '',
			// 问答相关
			question: '',
			messages: [],
			asking: false,
			// scrollspy 预计算的每组偏移量（相对滚动容器顶部）
			groupOffsets: []
		}
	},
	computed: {
		grouped() {
			const groups = []
			for (const cat of this.allCategories) {
				if (cat === '全部') continue
				const teas = this.teaList.filter(t => t.category === cat)
				if (teas.length > 0) {
					groups.push({ category: cat, teas })
				}
			}
			const known = new Set(this.allCategories)
			const others = this.teaList.filter(t => !known.has(t.category))
			if (others.length > 0) {
				groups.push({ category: '其他', teas: others })
			}
			return groups
		}
	},
	onLoad() {
		this.loadTea()
	},
	watch: {
		grouped() {
			this.$nextTick(() => this.calcGroupOffsets())
		}
	},
	methods: {
		async loadTea() {
			this.loading = true
			try {
				this.teaList = await getTeaList('')
			} catch (e) {
				console.error('加载茶品失败', e)
				uni.showToast({ title: '加载失败，请确认后端已启动', icon: 'none' })
			} finally {
				this.loading = false
			}
		},
		switchTab(tab) {
			this.currentTab = tab
		},
		calcGroupOffsets() {
			// 用 createSelectorQuery 链式测量：一次 exec 拿全部结果（标准用法）
			setTimeout(() => {
				uni.createSelectorQuery().in(this)
					.selectAll('.group')
					.boundingClientRect()
					.select('.tea-scroll')
					.boundingClientRect()
					.exec((res) => {
						const rects = res && res[0]
						const containerRect = res && res[1]
						if (!rects || !rects.length || !containerRect) return
						const base = containerRect.top
						this.groupOffsets = rects.map(r => r.top - base)
					})
			}, 400)
		},
		jumpToCategory(cat) {
			this.activeCategory = cat
			if (cat === '全部') {
				// 回到顶部：滚动到 top 锚点
				this.scrollToId = ''
				this.$nextTick(() => {
					this.scrollToId = 'top'
				})
				return
			}
			const idx = this.grouped.findIndex(g => g.category === cat)
			if (idx >= 0) {
				this.scrollToId = 'cat-' + idx
			}
		},
		onScroll(e) {
			// scroll-view 标准事件：e.detail.scrollTop
			const scrollTop = (e.detail && e.detail.scrollTop) || 0
			const groups = this.grouped
			if (!groups.length) return

			// 如果偏移量还没测到，现场补测一次
			if (!this.groupOffsets.length) {
				this.calcGroupOffsets()
				return
			}

			// 找最后一个 offset <= scrollTop 的分组（即当前滚到哪个分类了）
			let current = '全部'
			for (let i = 0; i < groups.length; i++) {
				const offset = this.groupOffsets[i]
				if (offset !== undefined && scrollTop >= offset) {
					current = groups[i].category
				}
			}
			if (current !== this.activeCategory) {
				this.activeCategory = current
			}
		},
		goDetail(id) {
			uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })
		},
		async send() {
			const q = this.question.trim()
			if (!q || this.asking) return
			// 历史 = 当前消息列表（不含刚加入的这条 user 消息）
			const history = this.messages.map(m => ({ role: m.role, content: m.content }))
			this.messages.push({ role: 'user', content: q })
			this.question = ''
			this.asking = true
			this.scrollChatBottom()
			try {
				const res = await askQuestion(q, history)
				this.messages.push({
					role: 'assistant',
					content: res.answer,
					sources: res.sources || []
				})
			} catch (e) {
				this.messages.push({
					role: 'assistant',
					content: '问答失败，请确认 AI 服务已启动（端口 8000）'
				})
			} finally {
				this.asking = false
				this.scrollChatBottom()
			}
		},
		scrollChatBottom() {
			setTimeout(() => {
				const el = this.$refs.chatArea
				if (el) {
					el.scrollTop = el.scrollHeight
				}
			}, 100)
		}
	}
}
</script>

<style scoped>
.layout {
	display: flex;
	height: 100%;
	overflow: hidden;
}

/* ===== 一级导航 ===== */
.sidebar {
	width: 150rpx;
	flex-shrink: 0;
	display: flex;
	flex-direction: column;
	background: #f0f0eb;
	border-right: 1rpx solid #e0e0d8;
}

.side-main {
	padding: 40rpx 0;
	text-align: center;
	border-left: 6rpx solid transparent;
}

.side-main.active {
	background: #ffffff;
	border-left: 6rpx solid #1a6b4a;
}

.side-main-text {
	font-size: 30rpx;
	font-weight: bold;
	color: #4a4a4a;
}

.side-main.active .side-main-text {
	color: #1a6b4a;
}

/* ===== 二级分类栏 ===== */
.sub-sidebar {
	width: 180rpx;
	flex-shrink: 0;
	background: #f7f7f3;
	border-right: 1rpx solid #e0e0d8;
	overflow-y: auto;
}

.sub-item {
	padding: 26rpx 20rpx;
	border-left: 6rpx solid transparent;
}

.sub-item.active {
	background: #ffffff;
	border-left: 6rpx solid #1a6b4a;
}

.sub-text {
	font-size: 27rpx;
	color: #4a4a4a;
}

.sub-item.active .sub-text {
	color: #1a6b4a;
	font-weight: bold;
}

/* ===== 内容区 ===== */
.content {
	flex: 1;
	min-width: 0;
	min-height: 0;
	position: relative;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.tea-scroll {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	position: relative; /* 关键：让子元素 offsetTop 相对本容器计算 */
}

.group {
	padding: 10rpx 20rpx;
}

.group-title {
	padding: 20rpx 0 10rpx;
	font-size: 34rpx;
	font-weight: bold;
	color: #1a6b4a;
}

.tea-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 26rpx;
	margin-bottom: 16rpx;
	border-radius: 16rpx;
	background: #ffffff;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.tea-card-left {
	display: flex;
	flex-direction: column;
}

.tea-name {
	font-size: 34rpx;
	font-weight: bold;
	color: #2c2c2c;
}

.tea-origin {
	margin-top: 8rpx;
	font-size: 26rpx;
	color: #9a9a9a;
}

.tea-card-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}

.tea-std {
	font-size: 22rpx;
	color: #b0b0b0;
}

.loading,
.empty {
	padding: 100rpx 0;
	text-align: center;
	color: #9a9a9a;
	font-size: 28rpx;
}

/* ===== 问答区 ===== */
.ask-wrap {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.chat-area {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	padding: 20rpx;
	box-sizing: border-box;
}

.msg-row {
	display: flex;
	margin-bottom: 24rpx;
}

.msg-row.user {
	justify-content: flex-end;
}

.msg-row.assistant {
	justify-content: flex-start;
}

.bubble {
	max-width: 82%;
	padding: 22rpx 28rpx;
	border-radius: 16rpx;
	font-size: 32rpx;
	line-height: 1.7;
}

.user .bubble {
	background: #1a6b4a;
	color: #ffffff;
	border-top-right-radius: 4rpx;
}

.assistant .bubble {
	background: #ffffff;
	color: #2c2c2c;
	border-top-left-radius: 4rpx;
	box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.05);
}

.msg-text {
	display: block;
}

.msg-sources {
	display: block;
	margin-top: 12rpx;
	font-size: 24rpx;
	color: #9a9a9a;
}

.input-bar {
	display: flex;
	align-items: center;
	flex-shrink: 0;
	padding: 16rpx 20rpx;
	background: #ffffff;
	border-top: 1rpx solid #eee;
}

.input {
	flex: 1;
	height: 80rpx;
	padding: 0 24rpx;
	border-radius: 40rpx;
	background: #f5f5f0;
	font-size: 32rpx;
}

.send-btn {
	margin-left: 16rpx;
	background: #1a6b4a;
	color: #ffffff;
}
</style>
