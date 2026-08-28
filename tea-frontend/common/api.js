/**
 * API 统一封装：后端地址、请求方法。
 * 后端两个服务：SpringBoot(8080) + Python RAG(8000)
 */

// SpringBoot 后端
const BACKEND_BASE = 'http://127.0.0.1:8080'
// Python RAG 服务
const AI_BASE = 'http://127.0.0.1:8000'

/**
 * 通用请求封装
 * @param {string} url 完整地址
 * @param {object} options uni.request 选项
 */
function request(url, options = {}) {
	return new Promise((resolve, reject) => {
		uni.request({
			url,
			method: options.method || 'GET',
			data: options.data || {},
			header: {
				'Content-Type': 'application/json',
				...(options.header || {})
			},
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
				} else {
					reject(new Error(res.data?.message || `请求失败 ${res.statusCode}`))
				}
			},
			fail: (err) => reject(err)
		})
	})
}

// ===== 茶品相关（SpringBoot） =====

/** 获取茶品列表 */
export function getTeaList(category = '') {
	const url = category ? `${BACKEND_BASE}/api/tea?category=${encodeURIComponent(category)}` : `${BACKEND_BASE}/api/tea`
	return request(url)
}

/** 获取茶品详情（含成分、风味） */
export function getTeaDetail(id) {
	return request(`${BACKEND_BASE}/api/tea/${id}/detail`)
}

// ===== 问答相关（Python RAG） =====

/** RAG 问答（history 为多轮对话历史，形如 [{role, content}]） */
export function askQuestion(question, history = []) {
	return request(`${AI_BASE}/ask`, {
		method: 'POST',
		data: { question, history }
	})
}

export { BACKEND_BASE, AI_BASE }
