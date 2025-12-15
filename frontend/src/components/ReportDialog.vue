<template>
  <el-dialog v-model="visible" title="举报" width="500px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="举报类别">
        <el-select v-model="form.category" placeholder="请选择">
          <el-option label="垃圾信息" value="spam" />
          <el-option label="骚扰/辱骂" value="abuse" />
          <el-option label="虚假信息" value="fake" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="严重级">
        <el-select v-model="form.severity" placeholder="请选择">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
        </el-select>
      </el-form-item>
      <el-form-item label="说明">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请填写详细说明"
        />
      </el-form-item>
      <el-form-item label="证据图片">
        <el-upload
          ref="uploadRef"
          :action="'http://localhost:5000/api/reports'"
          :headers="{ Authorization: `Bearer ${token}` }"
          name="image"
          :data="uploadData"
          :show-file-list="false"
          :auto-upload="false"
          :before-upload="beforeEvidenceUpload"
          :on-progress="handleProgress"
          :on-success="handleSuccess"
          :on-error="handleError"
        >
          <el-button>选择图片</el-button>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="uploadLoading" @click="submit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits, computed } from "vue";
import request from "../utils/request";
import { getToken } from "../utils/auth";
import { ElMessage } from "element-plus";

const props = defineProps({
  modelValue: Boolean,
  targetUserId: Number,
  itemId: Number,
});
const emit = defineEmits(["update:modelValue", "submitted"]);
const visible = ref(false);
const form = ref({ category: "spam", severity: "medium", description: "", anonymous: false });
const uploadRef = ref();
const token = getToken();
const uploadLoading = ref(false);
const uploadData = computed(() => ({
  target_user_id: props.targetUserId,
  item_id: props.itemId,
  category: form.value.category,
  severity: form.value.severity,
  description: form.value.description,
  anonymous: form.value.anonymous,
}));

watch(
  () => props.modelValue,
  (v) => {
    visible.value = v;
  }
);
watch(visible, (v) => emit("update:modelValue", v));

const submit = async () => {
  const files = uploadRef.value?.uploadFiles || [];
  if (files.length > 0) {
    uploadLoading.value = true;
    uploadRef.value.submit();
  } else {
    await request.post("/reports", {
      target_user_id: props.targetUserId,
      item_id: props.itemId,
      category: form.value.category,
      severity: form.value.severity,
      description: form.value.description,
      anonymous: form.value.anonymous,
    });
    ElMessage.success("举报已提交");
    emit("submitted");
    visible.value = false;
  }
};

const handleSuccess = () => {
  uploadLoading.value = false;
  ElMessage.success("证据图片上传成功，举报已提交");
  emit("submitted");
  visible.value = false;
};
const handleError = () => {
  uploadLoading.value = false;
  ElMessage.error("图片上传失败");
};
const handleProgress = () => {
  uploadLoading.value = true;
};
const beforeEvidenceUpload = (file) => {
  const isImage = file.type.startsWith("image/");
  const isLt10M = file.size / 1024 / 1024 <= 10;
  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }
  if (!isLt10M) {
    ElMessage.error("图片大小不能超过10MB！");
    return false;
  }
  return true;
};
</script>

<style scoped>
/* 对话框中的输入框样式 */
:deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

:deep(.el-dialog .el-input),
:deep(.el-dialog .el-select),
:deep(.el-dialog .el-textarea) {
  border: none !important;
  box-shadow: none !important;
}

:deep(.el-dialog .el-input__wrapper),
:deep(.el-dialog .el-select__wrapper),
:deep(.el-dialog .el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

:deep(.el-dialog .el-input__inner),
:deep(.el-dialog .el-textarea__inner),
:deep(.el-dialog .el-select__placeholder),
:deep(.el-dialog .el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

:deep(.el-dialog .el-input__wrapper.is-focus),
:deep(.el-dialog .el-textarea__inner:focus),
:deep(.el-dialog .el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

:deep(.el-dialog .el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

:deep(.el-dialog .el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

:deep(.el-dialog .el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}
</style>