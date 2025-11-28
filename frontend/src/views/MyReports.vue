<template>
  <div class="my-reports-container">
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <span>我的举报</span>
          <el-select
            v-model="status"
            placeholder="全部状态"
            size="small"
            @change="load"
          >
            <el-option label="全部" value="" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="打开" value="open" />
          </el-select>
        </div>
      </template>
      <el-empty v-if="reports.length === 0" description="暂无举报" />
      <el-table v-else :data="filtered" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="举报类别" width="120">
          <template #default="{ row }">{{
            categoryText(row.category)
          }}</template>
        </el-table-column>
        <el-table-column label="严重级" width="100">
          <template #default="{ row }">{{
            severityText(row.severity)
          }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">{{ statusText(row.status) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column label="被举报物品" width="220">
          <template #default="{ row }">
            <el-button
              v-if="row.item_id"
              type="text"
              @click="gotoItem(row.item_id)"
            >
              {{ row.item_title || "物品#" + row.item_id }}
            </el-button>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column label="证据" width="120">
          <template #default="{ row }">
            <el-image
              v-if="row.evidence_image_url"
              :src="absoluteUrl(row.evidence_image_url)"
              :preview-src-list="previewList(row.evidence_image_url)"
              style="width: 60px; height: 60px"
            />
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column prop="resolution_note" label="处理备注" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="editReport(row)" :disabled="row.status==='withdrawn'">修改举报</el-button>
            <el-button size="small" type="danger" @click="withdrawReport(row)" :disabled="row.status==='withdrawn'">撤回举报</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="editDialog" title="修改举报" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="举报类别">
          <el-select v-model="form.category">
            <el-option label="垃圾信息" value="spam" />
            <el-option label="骚扰/辱骂" value="abuse" />
            <el-option label="虚假信息" value="fake" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重级">
          <el-select v-model="form.severity">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="当前证据">
          <el-image
            v-if="form.evidence_image_url"
            :src="absoluteUrl(form.evidence_image_url)"
            :preview-src-list="[ absoluteUrl(form.evidence_image_url) ]"
            style="max-width: 100%"
          />
          <span v-else>暂无证据图片</span>
        </el-form-item>
        <el-form-item label="更新证据">
          <el-upload
            ref="uploadRef"
            :action="`${apiOrigin}/api/reports/${form.id}`"
            name="image"
            :headers="{ Authorization: `Bearer ${token}` }"
            :data="{
              category: form.category,
              severity: form.severity,
              description: form.description,
              anonymous: form.anonymous,
            }"
            :show-file-list="false"
            :auto-upload="false"
            :before-upload="beforeEvidenceUpload"
            :on-progress="handleUploadProgress"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
          >
            <el-button>选择图片</el-button>
          </el-upload>
          <el-button
            type="primary"
            plain
            style="margin-left: 8px"
            :loading="uploadLoading"
            @click="submitEvidenceUpload"
            >上传</el-button
          >
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import request, { absoluteUrl, apiOrigin, previewList } from "../utils/request";
import { useRouter } from "vue-router";
import { getToken } from "../utils/auth";
import { ElMessage } from "element-plus";

const reports = ref([]);
const status = ref("");
const load = async () => {
  const all = await request.get("/my-reports");
  // enrich item title via additional fetch when needed
  for (const r of all) {
    if (r.item_id) {
      try {
        const it = await request.get(`/items/${r.item_id}`);
        r.item_title = it.title;
      } catch {}
    }
  }
  reports.value = all;
};
const filtered = computed(() => {
  if (!status.value) return reports.value;
  return reports.value.filter((r) => r.status === status.value);
});
const router = useRouter();
const gotoItem = (id) => router.push(`/item/${id}`);
const categoryText = (c) =>
  ({ spam: "垃圾信息", abuse: "骚扰/辱骂", fake: "虚假信息", other: "其他" }[
    c
  ] || c);
const severityText = (s) => ({ low: "低", medium: "中", high: "高" }[s] || s);
const statusText = (st) =>
  ({
    open: "已举报",
    processing: "管理员处理中",
    resolved: "已解决",
    rejected: "管理员已拒绝",
    withdrawn: "你已撤回举报",
  }[st] || st);
const editDialog = ref(false);
const form = ref({
  id: 0,
  category: "spam",
  severity: "medium",
  description: "",
  evidence_image_url: "",
});
const uploadRef = ref();
const uploadLoading = ref(false);
const token = getToken();
const editReport = (row) => {
  form.value = {
    id: row.id,
    category: row.category,
    severity: row.severity,
    description: row.description,
    evidence_image_url: row.evidence_image_url,
  };
  editDialog.value = true;
};
const submitEdit = async () => {
  await request.put(`/reports/${form.value.id}`, {
    category: form.value.category,
    severity: form.value.severity,
    description: form.value.description,
  });
  editDialog.value = false;
  await load();
};
const submitEvidenceUpload = () => {
  uploadLoading.value = true;
  uploadRef.value?.submit();
};
const handleUploadSuccess = async () => {
  uploadLoading.value = false;
  ElMessage.success("证据图片上传成功");
  editDialog.value = false;
  await load();
};
const handleUploadError = () => {
  uploadLoading.value = false;
  ElMessage.error("图片上传失败");
};
const handleUploadProgress = () => { uploadLoading.value = true };
const beforeEvidenceUpload = (file) => {
  const isImage = file.type.startsWith("image/");
  const isLt10M = file.size / 1024 / 1024 <= 10;
  if (!isImage) { ElMessage.error("只能上传图片文件！"); return false }
  if (!isLt10M) { ElMessage.error("图片大小不能超过10MB！"); return false }
  return true;
};
const withdrawReport = async (row) => {
  await request.put(`/reports/${row.id}`, { withdraw: true });
  await load();
};
onMounted(load);
</script>

<style scoped>
.my-reports-container {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
