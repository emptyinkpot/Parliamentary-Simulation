/// Diplomatic relation level between two countries (-200 to +200 mapped to 5 tiers)
public enum DiplomaticRelation
{
    Alliance,
    Friendly,
    Neutral,
    Rival,
    Hostile
}

/// Treaty type that can be signed between countries
public enum TreatyType
{
    NonAggression,
    MilitaryAlliance,
    TradeAgreement,
    Vassalage,
    DefensivePact
}

/// Diplomatic action a country can perform toward another
public enum DiplomaticAction
{
    ImproveRelations,
    Insult,
    Warn,
    GuaranteeIndependence,
    DeclareWar,
    OfferPeace
}
