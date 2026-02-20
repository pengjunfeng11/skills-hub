<template>
  <el-container style="min-height: 100vh">
    <el-aside width="220px" style="background: #304156">
      <div style="padding: 20px; text-align: center; color: #fff; font-size: 18px; font-weight: bold;">
        Skills Hub
      </div>
      <el-menu
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/skills">
          <el-icon><Document /></el-icon>
          <span>Skills</span>
        </el-menu-item>
        <el-menu-item index="/teams">
          <el-icon><UserFilled /></el-icon>
          <span>团队</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: flex-end; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.08)">
        <span style="margin-right: 16px">{{ auth.user?.username }}</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>

      <el-main style="background: #f5f7fa">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

onMounted(() => {
  auth.fetchUser()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
