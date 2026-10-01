# Dicionário de dados canônico

Todos os CSV usam UTF-8, ponto decimal e IDs estáveis. Camadas espaciais usam CRS
declarado; cálculos métricos são feitos em CRS projetado apropriado. Toda tabela
possui `source_kind`, `source`, `estimation_method` e `is_estimated` quando houver
campos estimados.

## Entradas

### `road_nodes`
`node_id`, `longitude`, `latitude`, `geometry`, `crs`.

### `road_edges`
`edge_id`, `from_node`, `to_node`, `length_m`, `travel_time_s`, `speed_kph`,
`road_class`, `oneway`, `capacity_veh_h`, `flow_veh_h`, `access_restriction`,
`geometry`.

### `mobility_od`
`demand_id`, `origin_node`, `destination_node`, `timestamp`, `vehicles`,
`vehicle_type`, `trip_distance_km`, `trip_time_min`, `initial_soc`,
`battery_kwh`, `consumption_kwh_km`, `energy_required_kwh`, `requires_charge`.

### `transformers`
`transformer_id`, `primary_bus`, `secondary_bus`, `nominal_kva`,
`primary_kv`, `secondary_kv`, `base_loading_kva`, `power_factor`, `feeder_id`,
`customer_count`, `customer_type`, `longitude`, `latitude`.

O perfil longo usa `transformer_id`, `timestamp`, `active_kw`, `reactive_kvar`.

### `candidates`
`candidate_id`, `longitude`, `latitude`, `road_node_id`, `bus_id`,
`transformer_id`, `road_snap_distance_m`, `connection_distance_m`,
`connection_cost`, `available_area_m2`, `eligible`, `ineligibility_reason`.

### catálogos

Carregadores: `charger_type`, `nominal_kw`, `capex`, `opex_annual`, `efficiency`,
`lifetime_years`, `max_vehicle_kw`, `ports`, `electrical_requirements`.

Transformadores: `catalog_id`, `country`, `utility`, `nominal_kva`, `cost`,
`primary_kv`, `secondary_kv`, `phase`, `installation_requirements`.

## Saída obrigatória por transformador

| Campo | Unidade/descrição |
|---|---|
| `Transformer_ID` | identificador |
| `Potência_atual_kVA` | placa atual |
| `Carga_base_pico_kVA` | máximo cronológico sem VE |
| `Carga_EV_pico_kVA` | contribuição VE no instante crítico |
| `Carga_total_pico_kVA` | máximo cronológico conjunto |
| `Carregamento_atual_percentual` | base/nominal |
| `Carregamento_com_EV_percentual` | conjunto/nominal |
| `Margem_atual_kVA` | limite operacional menos pico base |
| `Potência_requerida_kVA` | pico/limite operacional |
| `Potência_recomendada_kVA` | menor classe comercial viável |
| `Necessita_upgrade` | booleano |
| `Custo_upgrade` | moeda/ano-base configurados |
| `Alimentador` | identificador |
| `Latitude`, `Longitude` | WGS84 para intercâmbio |

## Saída obrigatória por eletroposto

`Station_ID`, `Latitude`, `Longitude`, `Status_selecionado`,
`Número_de_carregadores`, `Tipo_de_carregador`, `Potência_unitária`,
`Potência_total`, `Energia_diária`, `Veículos_atendidos`, `Distância_média`,
`Tempo_médio_de_espera`, `Transformador_associado`,
`Carregamento_do_transformador`, `Custo_da_estação`,
`Custo_de_reforço_elétrico`.

`Potência_total` é instalada; não é sinônimo de demanda simultânea máxima, que é
armazenada separadamente nas séries horárias.
