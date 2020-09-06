# Database Structure

## Shops model

-   [] username
-   [] password
-   [] name
-   [] shop-id
-   [] inventory-id () = INVENTORY1
-   [] description = {location, sizeOfshop,etc}

## Users(Customer) model

-   [] name
-   [] phone (Use this as primary key)
-   [] order-id
-   [] wishlist-cart
-   [] shops-visited

## Products model

-   [] product-id
-   [] description -> {type, weight, color,}
-   [] product-name
-   [] wishlisted-times
-   [] price

## Inventory model

-   [] inventory-id INVENTORY1
-   [] inventory-list - [{product-quantity, product-id}]

## Orders model

-   [] Customer_id
-   [] shop_id
-   [] [products: quantity]
-   [] total

```


## Products model
{
 pid: P1
 name: maggi
},
{
    pid: P2,
    name: chocolate
}


## Inventory model - Example
{
iid : yajat
iil : [{quant: 10, pId : P1}]
},
{
iid : hrishekesh
iil : [{quant: 10, pId : P1}, {quant: 5, pId : P2}]
},
```

EndPoints:

-   [x] /login - POST - required -> {user_inp+, password+} | returned -> None
-   [x] /signup - POST - required -> {first_name, email+, username+, password+, confirmation+} | returned -> {inventory id}
-   [x] /logout - GET
-   [x] /addProduct - POST - required -> {product_id+, price+, quantity+, [description], product_name} | returned -> None
-   [x] /deleteProduct - POST - required -> {product_id+} | returned -> None
-   [x] /billingCheckout - POST - required -> {[orders]+, phone, name, [wishlist], location}
-   [x] /reBilling - POST - required -> {order_id+, [products]+} | returned -> Change (in billing amount)
-   [x] /getInventoryID - GET - returned -> {inventory_id}
-   [x] /addToWishlist - POST - required -> {phone+/customer_id}
-   [x] /dashboard - GET -> retuned -> {sold_today, active_inventory, quantity in hand, profit, most_selling}
-   [x] /soldToday - GET -> returned -> {[products], total}
-   [x] /activeInventory - GET -> returned -> {total%, [products]%}

<!-- {
name: "yajat",
phone: "9686221723",
location: "JP nagar", <--- given by program
order: {"product_id": quantity
}

} -->
