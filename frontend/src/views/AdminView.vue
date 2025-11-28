<template>
  <div class="admin-container">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名/标题"
          clearable
          class="toolbar-input"
          @keyup.enter="load"
        />
        <el-select
          v-model="reportStatus"
          placeholder="举报状态"
          class="toolbar-select"
          @change="load"
        >
          <el-option label="全部" value="" />
          <el-option label="处理中" value="processing" />
          <el-option label="已解决" value="resolved" />
          <el-option label="已拒绝" value="rejected" />
          <el-option label="已撤回" value="withdrawn" />
        </el-select>
        <el-select
          v-model="itemStatus"
          placeholder="物品状态"
          class="toolbar-select"
          @change="load"
        >
          <el-option label="全部" value="" />
          <el-option label="进行中" value="open" />
          <el-option label="已解决" value="closed" />
        </el-select>
        <el-button type="primary" @click="load">刷新</el-button>
        <el-button type="success" v-if="meLevel" @click="openCreateUser"
          >创建用户</el-button
        >
        <el-button type="success" v-if="meLevel" @click="openCreateItem"
          >创建物品</el-button
        >
      </div>
      <el-tabs v-model="tab">
        <el-tab-pane label="用户" name="users">
          <el-table :data="usersPaged" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column label="角色">
              <template #default="{ row }">
                <el-tag v-if="row.role === 'admin'" type="success"
                  >管理员</el-tag
                >
                <el-tag v-else>普通用户</el-tag>
                <el-tag
                  v-if="row.is_banned"
                  type="danger"
                  style="margin-left: 6px"
                  >已封禁</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="等级">
              <template #default="{ row }">
                {{ row.role === "admin" ? levelText(row.admin_level) : "无" }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="420">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="danger"
                  v-if="!row.is_banned && !isSelf(row)"
                  @click="banUser(row)"
                  >封禁</el-button
                >
                <el-button
                  size="small"
                  type="success"
                  v-else-if="row.is_banned && !isSelf(row)"
                  @click="unbanUser(row)"
                  >解封</el-button
                >
                <el-button size="small" @click="viewUser(row)">详情</el-button>
                <el-button
                  size="small"
                  type="warning"
                  v-if="row.role !== 'admin' && canAppointLow && !isSelf(row)"
                  @click="appoint(row, 'low')"
                  >任命低级</el-button
                >
                <el-button
                  size="small"
                  type="warning"
                  v-if="row.role !== 'admin' && canAppointMid && !isSelf(row)"
                  @click="appoint(row, 'mid')"
                  >任命中级</el-button
                >
                <el-button
                  size="small"
                  type="danger"
                  v-if="canRevoke(row) && !isSelf(row)"
                  @click="revoke(row)"
                  >解除任命</el-button
                >
                <el-button
                  size="small"
                  type="danger"
                  v-if="canDelete(row) && !isSelf(row)"
                  @click="deleteUser(row)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="usersPage"
              :page-size="pageSize"
              :total="usersFiltered.length"
              @current-change="
                (p) => {
                  usersPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="物品" name="items">
          <el-table :data="itemsPaged" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="title" label="标题" />
            <el-table-column label="类型">
              <template #default="{ row }">
                <el-tag>{{ categoryText(row.category) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'closed' ? 'success' : 'warning'"
                  >{{ statusText(row.status) }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="success"
                  v-if="row.status !== 'closed'"
                  @click="updateItemStatus(row, 'closed')"
                  >标记已解决</el-button
                >
                <el-button
                  size="small"
                  type="warning"
                  v-else
                  @click="updateItemStatus(row, 'open')"
                  >标记进行中</el-button
                >
                <el-button size="small" @click="viewItem(row)">详情</el-button>
                <el-button
                  size="small"
                  type="danger"
                  v-if="canDeleteItem"
                  @click="deleteItem(row)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="itemsPage"
              :page-size="pageSize"
              :total="itemsFiltered.length"
              @current-change="
                (p) => {
                  itemsPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="举报" name="reports">
          <el-table :data="reportsPaged" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="举报类别">
              <template #default="{ row }">{{
                reportCategoryText(row.category)
              }}</template>
            </el-table-column>
            <el-table-column label="严重级">
              <template #default="{ row }">{{
                severityText(row.severity)
              }}</template>
            </el-table-column>
            <el-table-column label="状态">
              <template #default="{ row }">{{
                statusReportText(row.status, row.user_withdrawn)
              }}</template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
            <el-table-column label="被举报物品" width="220">
              <template #default="{ row }">
                <el-button
                  v-if="row.item_id"
                  type="text"
                  @click="gotoItem(row)"
                >
                  {{ row.item_title || "物品#" + row.item_id }}（{{
                    categoryText(row.item_category)
                  }}）
                </el-button>
                <span v-else>无</span>
              </template>
            </el-table-column>
            <el-table-column label="举报用户" width="200">
              <template #default="{ row }">
                <span v-if="row.anonymous">此用户为匿名举报</span>
                <span v-else>{{ row.reporter_username || ('用户#'+row.reporter_id) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="被举报用户" width="200">
              <template #default="{ row }">
                <span>{{ row.target_username || (row.target_user_id ? ('用户#'+row.target_user_id) : '无') }}</span>
              </template>
            </el-table-column>
            <el-table-column label="证据" width="120">
              <template #default="{ row }">
                <el-image
                  v-if="row.evidence_image_url"
                  :src="absoluteUrl(row.evidence_image_url)"
                  :preview-src-list="[ absoluteUrl(row.evidence_image_url) ]"
                  style="width: 60px; height: 60px"
                />
                <span v-else>无</span>
              </template>
            </el-table-column>
            <el-table-column label="处理" width="360">
              <template #default="{ row }">
                <el-select
                  v-model="row.status"
                  placeholder="设置状态"
                  @change="updateReportStatus(row)"
                  :disabled="row.user_withdrawn"
                >
                  <el-option label="处理中" value="processing" />
                  <el-option label="已解决" value="resolved" />
                  <el-option label="已拒绝" value="rejected" />
                  <el-option label="举报已撤回" value="withdrawn" disabled />
                </el-select>
                <el-input
                  v-model="row.resolution_note"
                  placeholder="处理备注"
                  @change="updateReportStatus(row)"
                  style="margin-top: 6px"
                />
                <div
                  style="
                    margin-top: 6px;
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                  "
                >
                  <el-button
                    v-if="row.item_id"
                    type="danger"
                    size="small"
                    @click="adminDeleteReportedItem(row)"
                  >
                    删除此{{ categoryText(row.item_category) }}信息
                  </el-button>
                  <el-button
                    v-if="row.target_user_id"
                    type="warning"
                    size="small"
                    @click="adminBanReportedUser(row)"
                    >封禁被举报用户</el-button
                  >
                  <el-button
                    v-if="row.reporter_id"
                    type="warning"
                    size="small"
                    @click="adminBanReporter(row)"
                    >封禁举报用户</el-button
                  >
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="reportsPage"
              :page-size="pageSize"
              :total="reportsFiltered.length"
              @current-change="
                (p) => {
                  reportsPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="统计" name="stats">
          <div class="stats">
            <el-card class="stat-card" v-for="(v, k) in stats" :key="k">
              <div class="stat-title">{{ statText(k) }}</div>
              <div class="stat-value">{{ v }}</div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-dialog v-model="userDialog" title="用户详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="头像">
              <el-avatar
                :size="60"
                :src="currentUser?.avatar_url ? absoluteUrl(currentUser.avatar_url) : ''"
              />
        </el-descriptions-item>
        <el-descriptions-item label="用户名">{{
          currentUser?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{
          currentUser?.email
        }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{
          currentUser?.phone || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="院系">{{
          currentUser?.department || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="年级">{{
          currentUser?.grade_display || currentUser?.grade || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{
          currentUser?.class_name || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{
          currentUser?.student_id || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{
          genderText(currentUser?.gender)
        }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{
          roleText(currentUser?.role)
        }}</el-descriptions-item>
        <el-descriptions-item label="等级">{{
          levelText(currentUser?.admin_level)
        }}</el-descriptions-item>
        <el-descriptions-item label="加入时间">{{
          currentUser?.created_at
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    <el-dialog v-model="itemDialog" title="物品详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{
          currentItem?.title
        }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{
          categoryText(currentItem?.category)
        }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{
          statusText(currentItem?.status)
        }}</el-descriptions-item>
        <el-descriptions-item label="物品类型">{{
          currentItem?.item_type
        }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{
          currentItem?.location
        }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{
          currentItem?.contact_name
        }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{
          currentItem?.contact_phone
        }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{
          currentItem?.date
        }}</el-descriptions-item>
        <el-descriptions-item label="发布人">{{
          currentItem?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="发布时间">{{
          currentItem?.created_at
        }}</el-descriptions-item>
        <el-descriptions-item label="图片">
          <img
            v-if="currentItem?.image_url"
            :src="absoluteUrl(currentItem.image_url)"
            style="max-width: 100%; border-radius: 8px"
          />
          <span v-else>无图片</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    <el-dialog v-model="createUserDialog" title="创建用户" width="600px">
      <el-form :model="newUser" label-width="100px">
        <el-form-item label="身份">
          <el-select v-model="newUser.identity" placeholder="请选择">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="newUser.identity==='teacher'" label="工号"><el-input v-model="newUser.staff_id" /></el-form-item>
        <el-form-item label="用户名"><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="newUser.email" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="newUser.phone" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" type="password" show-password /></el-form-item>
        <template v-if="newUser.identity==='student'">
          <el-form-item label="院系"><el-input v-model="newUser.department" /></el-form-item>
          <el-form-item label="年级">
            <el-select v-model="newUser.grade" placeholder="选择年级">
              <el-option label="大一" value="大一" />
              <el-option label="大二" value="大二" />
              <el-option label="大三" value="大三" />
              <el-option label="大四" value="大四" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级"><el-input v-model="newUser.class_name" /></el-form-item>
          <el-form-item label="学号"><el-input v-model="newUser.student_id" /></el-form-item>
          <el-form-item label="性别">
            <el-select v-model="newUser.gender" placeholder="选择性别(可选)">
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
              <el-option label="其他" value="other" />
              <el-option label="不透露" value="secret" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="createUserDialog=false">取消</el-button>
        <el-button type="primary" @click="submitCreateUser">创建</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="createItemDialog" title="创建物品" width="600px">
      <el-form :model="newItem" label-width="120px">
        <el-form-item label="归属用户ID"
          ><el-input v-model="newItem.user_id"
        /></el-form-item>
        <el-form-item label="标题"
          ><el-input v-model="newItem.title"
        /></el-form-item>
        <el-form-item label="描述"
          ><el-input v-model="newItem.description" type="textarea"
        /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newItem.category">
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-form-item>
        <el-form-item label="物品类型"
          ><el-input v-model="newItem.item_type"
        /></el-form-item>
        <el-form-item label="地点"
          ><el-input v-model="newItem.location"
        /></el-form-item>
        <el-form-item label="联系人"
          ><el-input v-model="newItem.contact_name"
        /></el-form-item>
        <el-form-item label="联系电话"
          ><el-input v-model="newItem.contact_phone"
        /></el-form-item>
        <el-form-item label="日期"
          ><el-date-picker
            v-model="newItem.date"
            type="date"
            value-format="YYYY-MM-DD"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createItemDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreateItem">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue";
import request, { absoluteUrl, previewList } from "../utils/request";
import { getUser } from "../utils/auth";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
const router = useRouter();
const tab = ref("users");
const users = ref([]);
const items = ref([]);
const reports = ref([]);
const stats = ref({});
const keyword = ref("");
const reportStatus = ref("");
const itemStatus = ref("");
const userDialog = ref(false);
const itemDialog = ref(false);
const currentUser = ref(null);
const currentItem = ref(null);
const pageSize = ref(10);
const usersPage = ref(1);
const itemsPage = ref(1);
const reportsPage = ref(1);
const me = getUser();
const meLevel = me?.admin_level || "";
const meId = me?.id || 0;
const canAppointLow = computed(() => meLevel === "mid" || meLevel === "high");
const canAppointMid = computed(() => meLevel === "high");
const canDeleteItem = computed(() => meLevel === "mid" || meLevel === "high");
const isSelf = (row) => row?.id === meId;
const canDelete = (row) => {
  if (!meLevel) return false;
  if (row.role === "admin" && row.admin_level) {
    const r = { low: 1, mid: 2, high: 3 };
    return r[meLevel] > r[row.admin_level];
  }
  return meLevel !== "low";
};
const canRevoke = (row) => {
  if (row.role !== "admin" || !row.admin_level) return false;
  if (!row.admin_appointed_by || row.admin_appointed_by !== meId) return false;
  if (row.admin_level === "low") return meLevel === "mid" || meLevel === "high";
  if (row.admin_level === "mid") return meLevel === "high";
  return false;
};
const categoryText = (c) =>
  c === "lost" ? "失物" : c === "found" ? "拾物" : c || "";
const statusText = (s) => (s === "closed" ? "已解决" : "进行中");
const roleText = (r) =>
  r === "admin" ? "管理员" : r === "banned" ? "已封禁" : "普通用户";
const genderText = (g) =>
  ({ male: "男", female: "女", other: "其他", secret: "不透露" }[g] ||
  "未填写");
const levelText = (l) =>
  ({ low: "低级", mid: "中级", high: "高级" }[l] || "无");
const statText = (k) =>
  ({
    users: "用户总数",
    items: "物品总数",
    lost: "失物数量",
    found: "拾物数量",
    closed: "已解决数量",
    reports_open: "未处理举报",
  }[k] || k);

const load = async () => {
  if (tab.value === "users") users.value = await request.get("/admin/users");
  if (tab.value === "items") items.value = await request.get("/admin/items");
  if (tab.value === "reports")
    reports.value = await request.get("/admin/reports", {
      params: { status: reportStatus.value },
    });
  if (tab.value === "stats") stats.value = await request.get("/admin/stats");
};

onMounted(load);
watch(tab, load);

const banUser = async (row) => {
  await request.put(`/admin/users/${row.id}/ban`, { ban: true });
  await load();
};
const unbanUser = async (row) => {
  await request.put(`/admin/users/${row.id}/ban`, { ban: false });
  await load();
};
const updateItemStatus = async (row, status) => {
  await request.put(`/admin/items/${row.id}/status`, { status });
  await load();
};
const updateReportStatus = async (row) => {
  await request.put(`/admin/reports/${row.id}`, {
    status: row.status,
    resolution_note: row.resolution_note,
  });
};
const adminDeleteReportedItem = async (row) => {
  await request.delete(`/admin/items/${row.item_id}`);
  await load();
};
const adminBanReportedUser = async (row) => {
  await request.put(`/admin/users/${row.target_user_id}/ban`, { ban: true });
  ElMessage.success(`已封禁被举报用户（${row.target_username || ("用户#" + row.target_user_id)}）`);
  await load();
};
const adminBanReporter = async (row) => {
  await request.put(`/admin/users/${row.reporter_id}/ban`, { ban: true });
  if (row.anonymous) {
    ElMessage.success('已封禁举报用户');
  } else {
    ElMessage.success(`已封禁举报用户（${row.reporter_username || ("用户#" + row.reporter_id)}）`);
  }
  await load();
};
const gotoItem = (row) => {
  router.push(`/item/${row.item_id}`);
};
const reportCategoryText = (c) =>
  ({ spam: "垃圾信息", abuse: "骚扰/辱骂", fake: "虚假信息", other: "其他" }[
    c
  ] || c);
const severityText = (s) => ({ low: "低", medium: "中", high: "高" }[s] || s);
const statusReportText = (st, withdrawn) => {
  if (withdrawn || st === "withdrawn") return "举报已撤回";
  return (
    {
      open: "已发布",
      processing: "处理中",
      resolved: "已解决",
      rejected: "已拒绝",
    }[st] || st
  );
};
const appoint = async (row, level) => {
  await request.post("/admin/appoint", { target_user_id: row.id, level });
  await load();
};
const revoke = async (row) => {
  await request.post("/admin/revoke", { target_user_id: row.id });
  await load();
};
const deleteUser = async (row) => {
  await request.delete(`/admin/users/${row.id}`);
  await load();
};
const deleteItem = async (row) => {
  await request.delete(`/admin/items/${row.id}`);
  await load();
};

const createUserDialog = ref(false);
const createItemDialog = ref(false);
const newUser = ref({
  identity: "student",
  staff_id: "",
  username: "",
  email: "",
  phone: "",
  password: "",
  department: "",
  grade: "",
  class_name: "",
  student_id: "",
  gender: "",
});
const newItem = ref({
  user_id: "",
  title: "",
  description: "",
  category: "lost",
  item_type: "",
  location: "",
  contact_name: "",
  contact_phone: "",
  date: "",
});
const openCreateUser = () => {
  createUserDialog.value = true;
};
const openCreateItem = () => {
  createItemDialog.value = true;
};
const submitCreateUser = async () => {
  await request.post("/admin/users/create", newUser.value);
  createUserDialog.value = false;
  newUser.value = {
    identity: "student",
    staff_id: "",
    username: "",
    email: "",
    phone: "",
    password: "",
    department: "",
    grade: "",
    class_name: "",
    student_id: "",
    gender: "",
  };
  await load();
};
const submitCreateItem = async () => {
  await request.post("/admin/items/create", newItem.value);
  createItemDialog.value = false;
  newItem.value = {
    user_id: "",
    title: "",
    description: "",
    category: "lost",
    item_type: "",
    location: "",
    contact_name: "",
    contact_phone: "",
    date: "",
  };
  await load();
};

const usersFiltered = computed(() => {
  if (!keyword.value) return users.value;
  return users.value.filter(
    (u) =>
      (u.username || "").includes(keyword.value) ||
      (u.email || "").includes(keyword.value)
  );
});
const usersPaged = computed(() => {
  const start = (usersPage.value - 1) * pageSize.value;
  return usersFiltered.value.slice(start, start + pageSize.value);
});
const itemsFiltered = computed(() => {
  let list = items.value;
  if (itemStatus.value)
    list = list.filter((i) => i.status === itemStatus.value);
  if (!keyword.value) return list;
  return list.filter((i) => (i.title || "").includes(keyword.value));
});
const itemsPaged = computed(() => {
  const start = (itemsPage.value - 1) * pageSize.value;
  return itemsFiltered.value.slice(start, start + pageSize.value);
});
const reportsFiltered = computed(() => {
  if (!keyword.value) return reports.value;
  return reports.value.filter(
    (r) =>
      (r.description || "").includes(keyword.value) ||
      (r.category || "").includes(keyword.value)
  );
});
const reportsPaged = computed(() => {
  const start = (reportsPage.value - 1) * pageSize.value;
  return reportsFiltered.value.slice(start, start + pageSize.value);
});
const viewUser = (row) => {
  currentUser.value = row;
  userDialog.value = true;
};
const viewItem = (row) => {
  currentItem.value = row;
  itemDialog.value = true;
};
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.stat-card {
  text-align: center;
}
.stat-title {
  font-weight: 600;
}
.stat-value {
  font-size: 24px;
}
</style>
<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}
</style>
const router = useRouter()
