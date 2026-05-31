using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ImperialStrategy.Economy;

/// Trade routes, resource production, tariffs, and trade node collection.
public static class TradeSystem
{
    // --- Data Structures ---

    [System.Serializable]
    public struct TradeRoute
    {
        public int FromProvinceId;
        public int ToProvinceId;
        public ResourceType Resource;
        public float Volume;
        public bool Active;
    }

    [System.Serializable]
    public struct TradeNode
    {
        public int NodeId;
        public string Name;
        public List<int> ConnectedProvinceIds;
        public int CollectorCountryId;
        public float TotalValue;
    }

    [System.Serializable]
    public struct ProvinceProduction
    {
        public int ProvinceId;
        public ResourceType Resource;
        public float BaseOutput;
    }

    // --- State ---

    private static List<TradeRoute> _routes = new();
    private static Dictionary<int, TradeNode> _nodes = new();
    private static List<ProvinceProduction> _production = new();
    private static Dictionary<int, EconomicPolicy> _countryPolicies = new();

    // --- Public API ---

    public static void SetTradePolicy(int countryId, EconomicPolicy policy)
    {
        _countryPolicies[countryId] = policy;
    }

    public static EconomicPolicy GetTradePolicy(int countryId)
    {
        return _countryPolicies.TryGetValue(countryId, out var p) ? p : EconomicPolicy.FreeMarket;
    }

    public static void AddTradeRoute(int fromProvince, int toProvince, ResourceType resource, float volume)
    {
        _routes.Add(new TradeRoute
        {
            FromProvinceId = fromProvince,
            ToProvinceId = toProvince,
            Resource = resource,
            Volume = volume,
            Active = true
        });
    }

    public static void RemoveTradeRoute(int fromProvince, int toProvince)
    {
        _routes.RemoveAll(r => r.FromProvinceId == fromProvince && r.ToProvinceId == toProvince);
    }

    public static void RegisterTradeNode(int nodeId, string name, List<int> provinceIds, int collectorCountryId)
    {
        _nodes[nodeId] = new TradeNode
        {
            NodeId = nodeId,
            Name = name,
            ConnectedProvinceIds = provinceIds,
            CollectorCountryId = collectorCountryId,
            TotalValue = 0f
        };
    }

    public static void SetProvinceProduction(int provinceId, ResourceType resource, float baseOutput)
    {
        _production.RemoveAll(p => p.ProvinceId == provinceId && p.Resource == resource);
        _production.Add(new ProvinceProduction
        {
            ProvinceId = provinceId,
            Resource = resource,
            BaseOutput = baseOutput
        });
    }

    public static IReadOnlyList<TradeRoute> GetActiveRoutes() => _routes.Where(r => r.Active).ToList();

    public static IReadOnlyList<TradeRoute> GetRoutesForCountry(int countryId)
    {
        var ownedProvinces = CountryData.All.TryGetValue(countryId, out var c)
            ? new HashSet<int>(c.OwnedProvinceIds)
            : new HashSet<int>();
        return _routes.Where(r =>
            ownedProvinces.Contains(r.FromProvinceId) ||
            ownedProvinces.Contains(r.ToProvinceId)).ToList();
    }

    /// Calculate tariff modifier based on trade policy.
    public static float GetTariffModifier(int countryId)
    {
        var policy = GetTradePolicy(countryId);
        return policy switch
        {
            EconomicPolicy.FreeMarket => 0f,
            EconomicPolicy.Protectionism => 0.25f,
            EconomicPolicy.Mercantilism => 0.40f,
            EconomicPolicy.Planned => 0.60f,
            _ => 0f
        };
    }

    /// Monthly tick: flow resources through trade nodes, apply tariffs.
    public static void Tick()
    {
        // Reset node values
        var nodeKeys = _nodes.Keys.ToList();
        foreach (int nid in nodeKeys)
        {
            var node = _nodes[nid];
            node.TotalValue = 0f;
            _nodes[nid] = node;
        }

        // Accumulate production into trade nodes
        foreach (var prod in _production)
        {
            foreach (var kvp in _nodes)
            {
                if (kvp.Value.ConnectedProvinceIds.Contains(prod.ProvinceId))
                {
                    var node = _nodes[kvp.Key];
                    node.TotalValue += prod.BaseOutput;
                    _nodes[kvp.Key] = node;
                    break;
                }
            }
        }

        // Apply trade route tariffs
        foreach (var route in _routes)
        {
            if (!route.Active) continue;
            int destOwner = GetProvinceOwner(route.ToProvinceId);
            float tariff = GetTariffModifier(destOwner);
            if (tariff > 0f && CountryData.All.TryGetValue(destOwner, out var dest))
                dest.Treasury += tariff * route.Volume;
        }

        // Credit collector countries from trade nodes
        foreach (var kvp in _nodes)
        {
            var node = kvp.Value;
            if (node.TotalValue > 0f && CountryData.All.TryGetValue(node.CollectorCountryId, out var collector))
            {
                float tariff = GetTariffModifier(node.CollectorCountryId);
                collector.Treasury += node.TotalValue * (0.1f + tariff * 0.05f);
            }
        }
    }

    // --- Helpers ---

    private static int GetProvinceOwner(int provinceId)
    {
        if (ProvinceData.IdLookup.TryGetValue(provinceId, out var prov))
            return prov.OwnerCountryId;
        return -1;
    }
}
