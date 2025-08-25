<script lang="ts" setup>
import aboutBg from '@/assets/embedded/LOGO-about.png'

import { ref, reactive, onMounted } from 'vue'
// License functionality removed
// import type { F2CLicense } from './index.ts'
// import { licenseApi } from '@/api/license'
// import { ElMessage } from 'element-plus-secondary'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user.ts'
const dialogVisible = ref(false)
const { t } = useI18n()
const userStore = useUserStore()

// Simplified license object for display
const license = reactive({
  status: 'valid',
  corporation: 'SQLBot Community Edition',
  expired: 'No Expiration',
  count: 0,
  version: 'Community',
  edition: 'Community',
  serialNo: '-',
  remark: 'Open Source Version',
  isv: '',
})

// const tipsSuffix = ref('')
const build = ref('1.0.0')
const isAdmin = ref(false)
// const fileList = reactive([])
// const dynamicCardClass = ref('')
// const loading = ref(false)

onMounted(() => {
  isAdmin.value = userStore.getUid === '1'
  // License functionality removed - no API calls needed
})

const open = () => {
  dialogVisible.value = true
}

defineExpose({
  open,
})
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="t('about.title')"
    width="840px"
    modal-class="about-dialog"
  >
    <div class="color-overlay flex-center">
      <img width="368" height="84" :src="aboutBg" />
    </div>
    <div class="content">
      <div class="item">
        <div class="label">{{ $t('about.auth_to') }}</div>
        <div class="value">{{ license.corporation }}</div>
      </div>
      <div v-if="license.isv" class="item">
        <div class="label">ISV</div>
        <div class="value">{{ license.isv }}</div>
      </div>
      <div class="item">
        <div class="label">{{ $t('about.expiration_time') }}</div>
        <div class="value" :class="{ 'expired-mark': license.status === 'expired' }">
          {{ license.expired }}
        </div>
      </div>
      <div class="item">
        <div class="label">{{ $t('about.version') }}</div>
        <div class="value">
          {{
            !license?.edition
              ? $t('about.standard')
              : license.edition === 'Embedded'
                ? $t('about.Embedded')
                : license.edition === 'Professional'
                  ? $t('about.Professional')
                  : $t('about.enterprise')
          }}
        </div>
      </div>
      <div class="item">
        <div class="label">{{ $t('about.version_num') }}</div>
        <div class="value">{{ build }}</div>
      </div>
      <div class="item">
        <div class="label">{{ $t('about.serial_no') }}</div>
        <div class="value">{{ license.serialNo || '-' }}</div>
      </div>
      <div class="item">
        <div class="label">{{ $t('about.remark') }}</div>
        <div class="value ellipsis">{{ license.remark || '-' }}</div>
      </div>

      <!-- License functionality removed -->
      <!-- 
      <div v-if="isAdmin" style="margin-top: 24px" class="lic_rooter">
        <el-upload
          action=""
          :multiple="false"
          :show-file-list="false"
          :file-list="fileList"
          accept=".key"
          name="file"
          :before-upload="beforeUpload"
        >
          <el-button plain> {{ $t('about.update_license') }} </el-button>
        </el-upload>
      </div>
      -->
    </div>
    <div class="name">2014-2025 版权所有 © 杭州飞致云信息科技有限公司</div>
  </el-dialog>
</template>

<style lang="less">
.about-dialog {
  .color-overlay {
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    background: var(--ed-color-primary-1a, #1cba901a);
    border: 1px solid #dee0e3;
    border-bottom: 0;
    height: 180px;
  }

  .name {
    font-weight: 400;
    font-size: 12px;
    line-height: 22px;
    text-align: center;
    margin-top: 16px;
    color: #8f959e;
  }

  .content {
    border-radius: 6px;
    border: 1px solid #dee0e3;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    border-top: 0;
    padding: 24px 40px;

    .item {
      font-size: 16px;
      font-style: normal;
      font-weight: 400;
      line-height: 24px;
      margin-bottom: 16px;
      display: flex;
      font-weight: 400;
      .expired-mark {
        color: red;
      }
      .label {
        color: #646a73;
        width: 240px;
      }

      .value {
        margin-left: 24px;
        max-width: 448px;
      }
    }
  }
}
.lic_rooter {
  flex-direction: row;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  align-content: center;
  width: fit-content;
  justify-content: space-between;
  column-gap: 12px;
}
</style>
