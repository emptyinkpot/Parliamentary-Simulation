using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ImperialStrategy.Economy;

/// Building construction, effects, slots, and wartime destruction.
public static class BuildingSystem
{
    // --- Data Structures ---

    [System.Serializable]
    public struct BuildingDefinition
    {
        public BuildingType Type;
        public float Cost;
        public int ConstructionMonths;
        public ResourceType ProducedResource;
        public float ProductionBonus;
    }

    [System.Serializable]
    public struct BuildingInstance
    {
        public int ProvinceId;
        public BuildingType Type;
        public int RemainingMonths; // 0 = completed
        public bool Destroyed;
    }

    // --- State ---

    private static List<BuildingInstance> _buildings = new();
    private static Dictionary<BuildingType, BuildingDefinition> _definitions = new();

    // --- Initialization ---

    static BuildingSystem()
    {
        RegisterDefaults();
    }

    private static void RegisterDefaults()
    {
        Define(BuildingType.Farm, 50f, 2, ResourceType.Food, 1.5f);
        Define(BuildingType.Mine, 80f, 3, ResourceType.Iron, 2.0f);
        Define(BuildingType.Factory, 120f, 4, ResourceType.Coal, 2.5f);
        Define(BuildingType.Port, 100f, 3, ResourceType.Gold, 1.0f);
        Define(BuildingType.Fortress, 200f, 6, ResourceType.MilitarySupply, 1.0f);
        Define(BuildingType.University, 150f, 5, ResourceType.Luxury, 0.5f);
        Define(BuildingType.Market, 60f, 2, ResourceType.Gold, 1.5f);
        Define(BuildingType.Barracks, 90f, 3, ResourceType.MilitarySupply, 2.0f);
    }

    private static void Define(BuildingType type, float cost, int months, ResourceType resource, float bonus)
    {
        _definitions[type] = new BuildingDefinition
        {
            Type = type,
            Cost = cost,
            ConstructionMonths = months,
            ProducedResource = resource,
            ProductionBonus = bonus
        };
    }

    // --- Public API ---

    /// Maximum building slots for a province based on population (development proxy).
    public static int GetMaxSlots(int provinceId)
    {
        if (!ProvinceData.IdLookup.TryGetValue(provinceId, out var prov))
            return 0;
        // 1 slot per 500 population, minimum 1, maximum 10
        return Mathf.Clamp(prov.Population / 500, 1, 10);
    }

    /// Current number of buildings (including under construction) in a province.
    public static int GetUsedSlots(int provinceId)
    {
        return _buildings.Count(b => b.ProvinceId == provinceId && !b.Destroyed);
    }

    /// Attempt to start construction. Returns true if successful.
    public static bool StartConstruction(int provinceId, BuildingType type, int ownerCountryId)
    {
        if (!_definitions.TryGetValue(type, out var def))
            return false;

        if (GetUsedSlots(provinceId) >= GetMaxSlots(provinceId))
            return false;

        if (!CountryData.All.TryGetValue(ownerCountryId, out var country))
            return false;

        if (country.Treasury < def.Cost)
            return false;

        country.Treasury -= def.Cost;
        _buildings.Add(new BuildingInstance
        {
            ProvinceId = provinceId,
            Type = type,
            RemainingMonths = def.ConstructionMonths,
            Destroyed = false
        });
        return true;
    }

    /// Get all completed buildings in a province.
    public static List<BuildingInstance> GetBuildings(int provinceId)
    {
        return _buildings.Where(b => b.ProvinceId == provinceId && !b.Destroyed && b.RemainingMonths == 0).ToList();
    }

    /// Get production bonus for a resource in a province from buildings.
    public static float GetProductionBonus(int provinceId, ResourceType resource)
    {
        float bonus = 0f;
        foreach (var b in _buildings)
        {
            if (b.ProvinceId != provinceId || b.Destroyed || b.RemainingMonths > 0)
                continue;
            if (_definitions.TryGetValue(b.Type, out var def) && def.ProducedResource == resource)
                bonus += def.ProductionBonus;
        }
        return bonus;
    }

    /// Destroy a random building in a province (war damage).
    public static bool DestroyBuilding(int provinceId)
    {
        var candidates = _buildings
            .Select((b, i) => (b, i))
            .Where(x => x.b.ProvinceId == provinceId && !x.b.Destroyed)
            .ToList();

        if (candidates.Count == 0) return false;

        int idx = candidates[Random.Range(0, candidates.Count)].i;
        var building = _buildings[idx];
        building.Destroyed = true;
        _buildings[idx] = building;
        return true;
    }

    /// Monthly tick: advance construction timers.
    public static void Tick()
    {
        for (int i = 0; i < _buildings.Count; i++)
        {
            var b = _buildings[i];
            if (b.Destroyed || b.RemainingMonths <= 0) continue;
            b.RemainingMonths--;
            _buildings[i] = b;
        }
    }

    /// Get the definition for a building type.
    public static BuildingDefinition? GetDefinition(BuildingType type)
    {
        return _definitions.TryGetValue(type, out var def) ? def : null;
    }
}

