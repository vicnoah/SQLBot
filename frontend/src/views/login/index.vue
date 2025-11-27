<template>
  <div class="login-container">
    <div class="login-left">
      <img :src="bg" alt="" />
    </div>
    <div class="login-content">
      <div class="login-right">
        <div class="login-logo-icon">
          <img height="52" v-if="loginBg" :src="loginBg" alt="" />
          <el-icon size="52" v-else
            ><custom_small v-if="appearanceStore.themeColor !== 'default'"></custom_small>
            <LOGO_fold v-else></LOGO_fold
          ></el-icon>
          <span style="margin-left: 14px; font-size: 34px; font-weight: 900; color: #485559">{{
            appearanceStore.name
          }}</span>
        </div>
        <div v-if="appearanceStore.getShowSlogan" class="welcome">
          {{ appearanceStore.slogan || $t('common.intelligent_questioning_platform') }}
        </div>
        <div v-else class="welcome" style="height: 0"></div>
        <div class="login-form">
          <h2 class="title">{{ $t('common.login') }}</h2>
          <el-form
            ref="loginFormRef"
            class="form-content_error"
            :model="loginForm"
            :rules="rules"
            @keyup.enter="submitForm"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                clearable
                :placeholder="$t('common.your_account_email_address')"
                size="large"
              ></el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                :placeholder="$t('common.enter_your_password')"
                type="password"
                show-password
                clearable
                size="large"
              ></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="login-btn" @click="submitForm">{{
                $t('common.login_')
              }}</el-button>
            </el-form-item>
            
            <!-- 企业微信登录面板 -->
            <div v-if="weWorkEnabled" class="wework-login-container">
              <div class="divider">
                <span>或</span>
              </div>
              <div id="ww_login" class="ww-login-panel"></div>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'
import { AuthApi } from '@/api/login'
import { ElMessage } from 'element-plus'
import * as ww from '@wecom/jssdk'
import { WWLoginType, WWLoginRedirectType } from '@wecom/jssdk'
import custom_small from '@/assets/svg/logo-custom_small.svg'
import LOGO_fold from '@/assets/LOGO-fold.svg'
import login_image from '@/assets/embedded/login_image.png'
import { useAppearanceStoreWithOut } from '@/stores/appearance'
import loginImage from '@/assets/blue/login-image_blue.png'

const router = useRouter()
const userStore = useUserStore()
const appearanceStore = useAppearanceStoreWithOut()
const { t } = useI18n()

const loginForm = ref({
  username: '',
  password: '',
})

// 企业微信登录相关
const weWorkEnabled = ref(false)
const weWorkConfig = ref<any>(null)
let wwLoginPanel: any = null

const bg = computed(() => {
  return appearanceStore.getBg || (appearanceStore.isBlue ? loginImage : login_image)
})

const loginBg = computed(() => {
  return appearanceStore.getLogin
})

const rules = {
  username: [{ required: true, message: t('common.your_account_email_address'), trigger: 'blur' }],
  password: [{ required: true, message: t('common.the_correct_password'), trigger: 'blur' }],
}

const loginFormRef = ref()

const submitForm = () => {
  loginFormRef.value.validate((valid: boolean) => {
    if (valid) {
      userStore.login(loginForm.value).then(() => {
        router.push('/chat')
      })
    }
  })
}

// 初始化企业微信登录组件
const initWeWorkLoginPanel = async () => {
  try {
    const config = await AuthApi.getWeWorkConfig()
    console.log('企业微信配置:', config)
    weWorkEnabled.value = config.enabled
    
    if (!config.enabled) {
      console.log('企业微信登录未启用')
      return
    }
    
    // 检查必要的配置项
    if (!config.corpId || !config.agentId) {
      console.error('企业微信配置不完整:', config)
      ElMessage.warning('企业微信登录配置不完整,请联系管理员')
      weWorkEnabled.value = false
      return
    }
    
    weWorkConfig.value = config
    
    // 等待下一个 tick,确保 DOM 已经渲染
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 检查挂载元素是否存在
    const mountEl = document.querySelector('#ww_login')
    if (!mountEl) {
      console.error('企业微信登录挂载元素不存在')
      return
    }
    
    console.log('开始创建企业微信登录面板...')
    // 使用 @wecom/jssdk 创建登录面板
    wwLoginPanel = ww.createWWLoginPanel({
      el: '#ww_login',
      params: {
        login_type: WWLoginType.corpApp,
        appid: config.corpId,
        agentid: config.agentId,
        redirect_uri: window.location.origin + '/login',
        state: 'LOGIN_STATE',
        redirect_type: WWLoginRedirectType.callback, // 使用回调方式
      },
      onCheckWeComLogin({ isWeComLogin }: any) {
        console.log('企业微信桌面端登录状态:', isWeComLogin)
      },
      onLoginSuccess: async ({ code }: any) => {
        console.log('企业微信登录成功, code:', code)
        try {
          const res = await AuthApi.weWorkCallback(code, 'LOGIN_STATE')
          userStore.setToken(res.access_token)
          await userStore.info()
          router.push('/chat')
        } catch (error: any) {
          ElMessage.error(error.message || '企业微信登录失败')
        }
      },
      onLoginFail: (err: any) => {
        console.error('企业微信登录失败:', err)
        ElMessage.error(`登录失败: ${err.errcode || ''} ${err.errmsg || ''}`)
      },
    })
    console.log('企业微信登录面板创建完成, panel:', wwLoginPanel)
  } catch (error) {
    console.error('初始化企业微信登录失败:', error)
    weWorkEnabled.value = false
  }
}

onMounted(() => {
  // 初始化企业微信登录面板
  initWeWorkLoginPanel()
})

onUnmounted(() => {
  // 组件销毁时卸载登录面板
  if (wwLoginPanel && wwLoginPanel.unmount) {
    wwLoginPanel.unmount()
  }
})
</script>

<style lang="less" scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;

  .login-left {
    display: flex;
    height: 100%;
    width: 40%;
    img {
      height: 100%;
      max-width: 100%;
    }
  }

  .login-content {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;

    .login-right {
      display: flex;
      align-items: center;
      flex-direction: column;
      position: relative;

      .login-logo-icon {
        width: auto;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .welcome {
        margin: 8px 0 40px 0;
        font-weight: 400;
        font-size: 14px;
        line-height: 20px;
        color: #646a73;
      }

      .login-form {
        border: 1px solid #dee0e3;
        padding: 40px;
        width: 480px;
        min-height: 392px;
        border-radius: 12px;
        box-shadow: 0px 6px 24px 0px #1f232914;

        .form-content_error {
          .ed-form-item--default {
            margin-bottom: 24px;
            &.is-error {
              margin-bottom: 48px;
            }
          }
        }

        .title {
          font-weight: 500;
          font-style: Medium;
          font-size: 20px;
          line-height: 28px;
          margin-bottom: 24px;
        }

        .login-btn {
          width: 100%;
          height: 45px;
          font-size: 16px;
          border-radius: 4px;
        }
        
        .wework-login-container {
          margin-top: 24px;
          
          .divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
            color: #999;
            
            &::before,
            &::after {
              content: '';
              flex: 1;
              height: 1px;
              background: #dee0e3;
            }
            
            span {
              padding: 0 12px;
              font-size: 14px;
            }
          }
          
          .ww-login-panel {
            display: flex;
            justify-content: center;
            min-height: 380px;
          }
        }

        .agreement {
          margin-top: 20px;
          text-align: center;
          color: #666;
        }
      }
    }
  }
}

:deep(.ed-input__wrapper) {
  background-color: #f5f7fa;
}
</style>
