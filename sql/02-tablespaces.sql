-- Phase 2.4 - 创建 Geo-Partitioning 表空间
-- 需要逐条执行（CREATE TABLESPACE 不支持事务块）

-- region1 表空间：副本只在 region1
CREATE TABLESPACE region1 WITH (
  replica_placement = '{
    "num_replicas": 1,
    "placement_blocks": [{
      "cloud": "cloud", "region": "region1", "zone": "zone", "min_num_replicas": 1
    }]
  }'
);

-- region2 表空间：副本只在 region2
CREATE TABLESPACE region2 WITH (
  replica_placement = '{
    "num_replicas": 1,
    "placement_blocks": [{
      "cloud": "cloud", "region": "region2", "zone": "zone", "min_num_replicas": 1
    }]
  }'
);

-- region3 表空间：副本只在 region3
CREATE TABLESPACE region3 WITH (
  replica_placement = '{
    "num_replicas": 1,
    "placement_blocks": [{
      "cloud": "cloud", "region": "region3", "zone": "zone", "min_num_replicas": 1
    }]
  }'
);

-- Leader Preference 表空间：RF=3，region1 优先读
CREATE TABLESPACE pref1 WITH (
  replica_placement = '{
    "num_replicas": 3,
    "placement_blocks": [
      { "cloud": "cloud", "region": "region1", "zone": "zone", "min_num_replicas": 1, "leader_preference": 1 },
      { "cloud": "cloud", "region": "region2", "zone": "zone", "min_num_replicas": 1, "leader_preference": 2 },
      { "cloud": "cloud", "region": "region3", "zone": "zone", "min_num_replicas": 1, "leader_preference": 3 }
    ]
  }'
);

-- 验证表空间
SELECT oid, spcname, spcoptions FROM pg_tablespace;

-- 创建分区表示例
CREATE TABLE user_eu (id INT PRIMARY KEY, data TEXT) TABLESPACE region1;
CREATE TABLE user_us (id INT PRIMARY KEY, data TEXT) TABLESPACE region2;
CREATE TABLE user_asia (id INT PRIMARY KEY, data TEXT) TABLESPACE region3;
