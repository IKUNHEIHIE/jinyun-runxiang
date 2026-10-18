<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import request from "@/api/request";
import { action, errorMessage } from "../teacher/shared";

const tab = ref("badges");
const badges = ref<any[]>([]);
const products = ref<any[]>([]);
const exchanges = ref<any[]>([]);
const loading = ref(false);
const busy = ref(false);
const error = ref("");

const badgeDialog = ref(false);
const badgeEditing = ref<any>(null);
const badgeForm = ref({
  code: "",
  name: "",
  description: "",
  icon_url: "",
  condition_text: "{}",
});

const productDialog = ref(false);
const productEditing = ref<any>(null);
const productForm = ref({
  name: "",
  category: "CULTURAL_CREATIVE",
  cover_url: "",
  origin_place: "",
  story: "",
  fund_rate_percent: 10,
  status: "ON_SALE",
  sku_name: "",
  price_yuan: 0,
  stock: 0,
});

const exchangeDialog = ref(false);
const exchangeEditing = ref<any>(null);
const exchangeForm = ref({
  name: "",
  cover_url: "",
  energy_cost: 100,
  stock: 10,
  status: "ACTIVE",
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [badges.value, products.value, exchanges.value] = await Promise.all([
      request.get("/admin/catalog/badges"),
      request.get("/admin/catalog/products"),
      request.get("/admin/catalog/exchange-items"),
    ]);
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}

function openBadge(row?: any) {
  badgeEditing.value = row || null;
  badgeForm.value = row
    ? {
        code: row.code,
        name: row.name,
        description: row.description,
        icon_url: row.icon_url,
        condition_text: JSON.stringify(row.condition_json || {}, null, 2),
      }
    : { code: "", name: "", description: "", icon_url: "", condition_text: "{}" };
  badgeDialog.value = true;
}

async function saveBadge() {
  let condition: any;
  try {
    condition = JSON.parse(badgeForm.value.condition_text || "{}");
  } catch {
    ElMessage.error("获得条件必须是合法 JSON");
    return;
  }
  if (!condition || typeof condition !== "object" || Array.isArray(condition)) {
    ElMessage.error("获得条件必须是 JSON 对象");
    return;
  }
  busy.value = true;
  await action(async () => {
    const payload = {
      code: badgeForm.value.code,
      name: badgeForm.value.name,
      description: badgeForm.value.description,
      icon_url: badgeForm.value.icon_url,
      condition_json: condition,
    };
    if (badgeEditing.value)
      await request.put(`/admin/catalog/badges/${badgeEditing.value.id}`, payload);
    else await request.post("/admin/catalog/badges", payload);
    ElMessage.success(badgeEditing.value ? "徽章已更新" : "徽章已创建");
    badgeDialog.value = false;
    await load();
  });
  busy.value = false;
}

async function removeBadge(row: any) {
  if (!window.confirm(`确定删除徽章「${row.name}」？已有用户获得的徽章不能删除。`))
    return;
  busy.value = true;
  await action(async () => {
    await request.delete(`/admin/catalog/badges/${row.id}`);
    ElMessage.success("徽章已删除");
    await load();
  });
  busy.value = false;
}

function openProduct(row?: any) {
  productEditing.value = row || null;
  productForm.value = row
    ? {
        name: row.name,
        category: row.category,
        cover_url: row.cover_url,
        origin_place: row.origin_place || "",
        story: row.story || "",
        fund_rate_percent: row.fund_rate_percent,
        status: row.status,
        sku_name: row.sku_name || row.name,
        price_yuan: (row.price_cents ?? 0) / 100,
        stock: row.stock ?? 0,
      }
    : {
        name: "",
        category: "CULTURAL_CREATIVE",
        cover_url: "",
        origin_place: "",
        story: "",
        fund_rate_percent: 10,
        status: "ON_SALE",
        sku_name: "",
        price_yuan: 0,
        stock: 0,
      };
  productDialog.value = true;
}

async function saveProduct() {
  busy.value = true;
  await action(async () => {
    const payload = {
      name: productForm.value.name,
      category: productForm.value.category,
      cover_url: productForm.value.cover_url,
      origin_place: productForm.value.origin_place || null,
      story: productForm.value.story || null,
      fund_rate_percent: productForm.value.fund_rate_percent,
      status: productForm.value.status,
      sku_name: productForm.value.sku_name || productForm.value.name,
      price_cents: Math.round(productForm.value.price_yuan * 100),
      stock: productForm.value.stock,
    };
    if (productEditing.value)
      await request.put(`/admin/catalog/products/${productEditing.value.id}`, payload);
    else await request.post("/admin/catalog/products", payload);
    ElMessage.success(productEditing.value ? "商品已更新" : "商品已创建");
    productDialog.value = false;
    await load();
  });
  busy.value = false;
}

function openExchange(row?: any) {
  exchangeEditing.value = row || null;
  exchangeForm.value = row
    ? {
        name: row.name,
        cover_url: row.cover_url || "",
        energy_cost: row.energy_cost,
        stock: row.stock,
        status: row.status,
      }
    : { name: "", cover_url: "", energy_cost: 100, stock: 10, status: "ACTIVE" };
  exchangeDialog.value = true;
}

async function saveExchange() {
  busy.value = true;
  await action(async () => {
    const payload = {
      name: exchangeForm.value.name,
      cover_url: exchangeForm.value.cover_url || null,
      energy_cost: exchangeForm.value.energy_cost,
      stock: exchangeForm.value.stock,
      status: exchangeForm.value.status,
    };
    if (exchangeEditing.value)
      await request.put(`/admin/catalog/exchange-items/${exchangeEditing.value.id}`, payload);
    else await request.post("/admin/catalog/exchange-items", payload);
    ElMessage.success(exchangeEditing.value ? "兑换商品已更新" : "兑换商品已创建");
    exchangeDialog.value = false;
    await load();
  });
  busy.value = false;
}

function money(cents: number | null) {
  return cents == null ? "—" : "¥" + (cents / 100).toFixed(2);
}

onMounted(load);
</script>

<template>
  <div class="catalog-view" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <span>目录管理：徽章 / 市集商品 / 能量兑换</span>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </template>
      <el-alert v-if="error" :title="error" type="error" :closable="false" />
      <el-tabs v-model="tab">
        <el-tab-pane label="徽章目录" name="badges">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="openBadge()">新增徽章</el-button>
          </div>
          <el-table :data="badges" stripe>
            <el-table-column prop="code" label="代码" min-width="210" />
            <el-table-column prop="name" label="名称" width="130" />
            <el-table-column prop="description" label="说明" min-width="240" />
            <el-table-column label="图标" width="90">
              <template #default="{ row }">
                <el-image :src="row.icon_url" style="width: 32px; height: 32px" fit="cover" />
              </template>
            </el-table-column>
            <el-table-column prop="holders" label="持有人数" width="100" />
            <el-table-column label="获得条件" min-width="220">
              <template #default="{ row }">
                <code class="condition">{{ JSON.stringify(row.condition_json) }}</code>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button link type="primary" @click="openBadge(row)">编辑</el-button>
                <el-button link type="danger" @click="removeBadge(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="市集商品" name="products">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="openProduct()">新增商品</el-button>
          </div>
          <el-table :data="products" stripe>
            <el-table-column prop="name" label="商品" min-width="180" />
            <el-table-column prop="category" label="分类" width="140" />
            <el-table-column label="价格" width="110">
              <template #default="{ row }">{{ money(row.price_cents) }}</template>
            </el-table-column>
            <el-table-column prop="stock" label="库存" width="90" />
            <el-table-column label="公益比例" width="100">
              <template #default="{ row }">{{ row.fund_rate_percent }}%</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'ON_SALE' ? 'success' : 'info'">
                  {{ row.status === "ON_SALE" ? "在售" : "下架" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="openProduct(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="能量兑换" name="exchanges">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="openExchange()">新增兑换商品</el-button>
          </div>
          <el-table :data="exchanges" stripe>
            <el-table-column prop="name" label="商品" min-width="180" />
            <el-table-column prop="energy_cost" label="能量" width="100" />
            <el-table-column prop="stock" label="库存" width="90" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
                  {{ row.status === "ACTIVE" ? "可兑换" : "已停用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="openExchange(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="badgeDialog" :title="badgeEditing ? '编辑徽章' : '新增徽章'" width="620px">
      <el-form label-position="top">
        <el-form-item label="徽章代码"><el-input v-model.trim="badgeForm.code" maxlength="64" /></el-form-item>
        <el-form-item label="名称"><el-input v-model.trim="badgeForm.name" maxlength="64" /></el-form-item>
        <el-form-item label="说明"><el-input v-model.trim="badgeForm.description" maxlength="255" /></el-form-item>
        <el-form-item label="图标 URL"><el-input v-model.trim="badgeForm.icon_url" maxlength="500" /></el-form-item>
        <el-form-item label="获得条件（JSON 对象）">
          <el-input v-model="badgeForm.condition_text" type="textarea" :rows="6" />
        </el-form-item>
        <el-button type="primary" :loading="busy" @click="saveBadge">保存</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="productDialog" :title="productEditing ? '编辑商品' : '新增商品'" width="680px">
      <el-form label-position="top">
        <el-form-item label="商品名称"><el-input v-model.trim="productForm.name" maxlength="128" /></el-form-item>
        <div class="form-grid">
          <el-form-item label="分类"><el-input v-model.trim="productForm.category" maxlength="32" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="productForm.status" style="width: 100%">
              <el-option label="在售" value="ON_SALE" />
              <el-option label="下架" value="OFF_SALE" />
            </el-select>
          </el-form-item>
          <el-form-item label="SKU 名称"><el-input v-model.trim="productForm.sku_name" maxlength="128" /></el-form-item>
          <el-form-item label="价格（元）"><el-input-number v-model="productForm.price_yuan" :min="0" :precision="2" /></el-form-item>
          <el-form-item label="库存"><el-input-number v-model="productForm.stock" :min="0" /></el-form-item>
          <el-form-item label="公益比例（%）"><el-input-number v-model="productForm.fund_rate_percent" :min="0" :max="100" /></el-form-item>
        </div>
        <el-form-item label="封面 URL"><el-input v-model.trim="productForm.cover_url" maxlength="500" /></el-form-item>
        <el-form-item label="产地"><el-input v-model.trim="productForm.origin_place" maxlength="128" /></el-form-item>
        <el-form-item label="商品故事"><el-input v-model="productForm.story" type="textarea" :rows="4" /></el-form-item>
        <el-button type="primary" :loading="busy" @click="saveProduct">保存</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="exchangeDialog" :title="exchangeEditing ? '编辑兑换商品' : '新增兑换商品'" width="560px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model.trim="exchangeForm.name" maxlength="128" /></el-form-item>
        <el-form-item label="封面 URL"><el-input v-model.trim="exchangeForm.cover_url" maxlength="500" /></el-form-item>
        <div class="form-grid">
          <el-form-item label="所需能量"><el-input-number v-model="exchangeForm.energy_cost" :min="1" /></el-form-item>
          <el-form-item label="库存"><el-input-number v-model="exchangeForm.stock" :min="0" /></el-form-item>
        </div>
        <el-form-item label="状态">
          <el-select v-model="exchangeForm.status" style="width: 100%">
            <el-option label="可兑换" value="ACTIVE" />
            <el-option label="已停用" value="INACTIVE" />
          </el-select>
        </el-form-item>
        <el-button type="primary" :loading="busy" @click="saveExchange">保存</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<style scoped>
.catalog-view {
  padding: 4px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toolbar {
  margin-bottom: 14px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 18px;
}
.condition {
  font-size: 12px;
  color: #5c6670;
  word-break: break-all;
}
</style>
