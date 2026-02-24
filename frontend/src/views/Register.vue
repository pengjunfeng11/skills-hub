<template>
  <div class="min-h-[100vh] flex items-center justify-center bg-gray-50 p-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl border border-gray-200 shadow-card p-8">
        <div class="text-center mb-8">
          <span class="material-icons-round text-primary text-[40px] mb-2">hub</span>
          <h1 class="text-2xl font-bold text-gray-900">注册账号</h1>
          <p class="text-sm text-gray-500 mt-1">创建你的 Skills Hub 账户</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
            <input
              v-model="form.username"
              placeholder="请输入用户名"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              placeholder="请输入邮箱"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-dark transition-colors disabled:opacity-60 cursor-pointer"
          >
            <span v-if="loading" class="material-icons-round text-[18px] animate-spin align-middle mr-1">progress_activity</span>
            注册
          </button>
        </form>

        <p class="text-center text-sm text-gray-500 mt-6">
          已有账号？
          <router-link to="/login" class="text-primary font-medium hover:underline">登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { register } from '../api'

const router = useRouter()
const toast = useToast()
const loading = ref(false)
const form = reactive({ username: '', email: '', password: '' })

async function handleRegister() {
  loading.value = true
  try {
    await register(form)
    toast.success('注册成功，请登录')
    router.push('/login')
  } catch (err) {
    toast.error(err.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>
