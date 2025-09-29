"""
Management command to seed the database with sample products and categories.

This command creates sample categories and products for development and testing purposes.
It's designed to be idempotent - running it multiple times won't create duplicates.

Usage:
    python manage.py seed_products
    python manage.py seed_products --clear  # Clear existing data first
    python manage.py seed_products --count 100  # Create 100 products instead of default 50
"""

import random
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductVariant, ProductReview

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample products and categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of products to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products and categories before seeding'
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Only create categories, skip products'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        count = options['count']
        clear = options['clear']
        categories_only = options['categories_only']
        
        try:
            with transaction.atomic():
                if clear:
                    self.clear_data()
                
                categories = self.create_categories()
                
                if not categories_only:
                    self.create_products(categories, count)
                    self.create_sample_reviews()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully seeded database with {len(categories)} categories'
                        + (f' and {count} products' if not categories_only else '')
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding database: {str(e)}')
            )
            raise CommandError(f'Failed to seed database: {str(e)}')

    def clear_data(self):
        """Clear existing products and categories."""
        self.stdout.write('Clearing existing data...')
        
        ProductReview.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        self.stdout.write(self.style.WARNING('Existing data cleared'))

    def create_categories(self):
        """Create sample categories with hierarchical structure."""
        self.stdout.write('Creating categories...')
        
        # Root categories
        categories_data = [
            ('Electronics', 'electronics', 'Electronic devices and gadgets'),
            ('Clothing', 'clothing', 'Fashion and apparel'),
            ('Home & Garden', 'home-garden', 'Home improvement and gardening'),
            ('Sports & Outdoors', 'sports-outdoors', 'Sports equipment and outdoor gear'),
            ('Books', 'books', 'Books and literature'),
            ('Health & Beauty', 'health-beauty', 'Health and beauty products'),
        ]
        
        root_categories = []
        for name, slug, description in categories_data:
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True
                }
            )
            root_categories.append(category)
            if created:
                self.stdout.write(f'  Created root category: {name}')

        # Subcategories
        subcategories_data = {
            'electronics': [
                ('Smartphones', 'smartphones', 'Mobile phones and accessories'),
                ('Laptops', 'laptops', 'Laptop computers'),
                ('Headphones', 'headphones', 'Audio equipment'),
                ('Cameras', 'cameras', 'Digital cameras and photography'),
            ],
            'clothing': [
                ('Men\'s Clothing', 'mens-clothing', 'Clothing for men'),
                ('Women\'s Clothing', 'womens-clothing', 'Clothing for women'),
                ('Shoes', 'shoes', 'Footwear for all occasions'),
                ('Accessories', 'accessories', 'Fashion accessories'),
            ],
            'home-garden': [
                ('Furniture', 'furniture', 'Home furniture'),
                ('Kitchen', 'kitchen', 'Kitchen appliances and tools'),
                ('Garden Tools', 'garden-tools', 'Gardening equipment'),
                ('Decor', 'decor', 'Home decoration items'),
            ],
            'sports-outdoors': [
                ('Fitness', 'fitness', 'Fitness equipment'),
                ('Camping', 'camping', 'Camping gear'),
                ('Water Sports', 'water-sports', 'Water sports equipment'),
                ('Team Sports', 'team-sports', 'Team sports equipment'),
            ],
            'books': [
                ('Fiction', 'fiction', 'Fiction books'),
                ('Non-Fiction', 'non-fiction', 'Non-fiction books'),
                ('Technical', 'technical', 'Technical and educational books'),
                ('Children', 'children', 'Children\'s books'),
            ],
            'health-beauty': [
                ('Skincare', 'skincare', 'Skincare products'),
                ('Makeup', 'makeup', 'Cosmetics and makeup'),
                ('Health Supplements', 'health-supplements', 'Vitamins and supplements'),
                ('Personal Care', 'personal-care', 'Personal hygiene products'),
            ],
        }
        
        all_categories = list(root_categories)
        
        for parent_slug, subcats in subcategories_data.items():
            parent = Category.objects.get(slug=parent_slug)
            for name, slug, description in subcats:
                category, created = Category.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'description': description,
                        'parent': parent,
                        'is_active': True
                    }
                )
                all_categories.append(category)
                if created:
                    self.stdout.write(f'  Created subcategory: {name} (under {parent.name})')
        
        return all_categories

    def create_products(self, categories, count):
        """Create sample products."""
        self.stdout.write(f'Creating {count} products...')
        
        # Sample product templates by category
        product_templates = {
            'smartphones': [
                'iPhone 15 Pro', 'Samsung Galaxy S24', 'Google Pixel 8', 'OnePlus 12',
                'Xiaomi Mi 14', 'Huawei P60 Pro', 'Sony Xperia 1 VI'
            ],
            'laptops': [
                'MacBook Pro M3', 'Dell XPS 13', 'ThinkPad X1 Carbon', 'HP Spectre x360',
                'ASUS ZenBook', 'Surface Laptop', 'Gaming Laptop ROG'
            ],
            'headphones': [
                'AirPods Pro', 'Sony WH-1000XM5', 'Bose QuietComfort', 'Sennheiser HD 650',
                'Audio-Technica ATH-M50x', 'Beats Studio3', 'JBL Live 650BTNC'
            ],
            'cameras': [
                'Canon EOS R5', 'Nikon D850', 'Sony A7 IV', 'Fujifilm X-T5',
                'Olympus OM-D E-M1', 'Panasonic Lumix GH6', 'Leica Q2'
            ],
            'mens-clothing': [
                'Classic Polo Shirt', 'Slim Fit Jeans', 'Cotton T-Shirt', 'Dress Shirt',
                'Casual Shorts', 'Hoodie Sweatshirt', 'Formal Suit'
            ],
            'womens-clothing': [
                'Summer Dress', 'Yoga Leggings', 'Blouse Top', 'Skinny Jeans',
                'Cardigan Sweater', 'Maxi Dress', 'Professional Blazer'
            ],
            'shoes': [
                'Running Sneakers', 'Leather Boots', 'High Heels', 'Casual Loafers',
                'Canvas Shoes', 'Hiking Boots', 'Ballet Flats'
            ],
            'furniture': [
                'Modern Sofa', 'Dining Table', 'Office Chair', 'Bookshelf',
                'Coffee Table', 'Wardrobe', 'Bed Frame'
            ],
            'kitchen': [
                'Stand Mixer', 'Coffee Machine', 'Air Fryer', 'Blender',
                'Microwave Oven', 'Rice Cooker', 'Food Processor'
            ],
            'fitness': [
                'Treadmill', 'Dumbbells Set', 'Yoga Mat', 'Exercise Bike',
                'Resistance Bands', 'Kettlebell', 'Pull-up Bar'
            ],
            'fiction': [
                'Mystery Novel', 'Romance Book', 'Sci-Fi Adventure', 'Fantasy Epic',
                'Thriller Story', 'Historical Fiction', 'Contemporary Novel'
            ],
            'skincare': [
                'Moisturizing Cream', 'Face Serum', 'Sunscreen SPF 50', 'Cleanser',
                'Eye Cream', 'Face Mask', 'Toner'
            ],
        }
        
        # Get leaf categories (categories without children)
        leaf_categories = [cat for cat in categories if not cat.children.exists()]
        
        created_count = 0
        for i in range(count):
            category = random.choice(leaf_categories)
            
            # Get product templates for this category
            templates = product_templates.get(category.slug, [f'{category.name} Product'])
            product_name = random.choice(templates)
            
            # Add variation to make it unique
            if i % len(templates) != 0:
                product_name += f' {random.choice(["Pro", "Plus", "Max", "Elite", "Premium", "Standard"])}'
            
            # Generate product data
            base_price = random.uniform(10, 2000)
            product_data = {
                'name': product_name,
                'slug': f'{product_name.lower().replace(" ", "-")}-{i+1}',
                'description': self.generate_product_description(product_name, category.name),
                'price': Decimal(str(round(base_price, 2))),
                'sku': f'{category.slug.upper()[:3]}-{str(i+1).zfill(4)}',
                'category': category,
                'stock': random.randint(0, 100),
                'weight': Decimal(str(round(random.uniform(0.1, 5.0), 2))),
                'dimensions_length': Decimal(str(round(random.uniform(5, 50), 1))),
                'dimensions_width': Decimal(str(round(random.uniform(5, 50), 1))),
                'dimensions_height': Decimal(str(round(random.uniform(1, 30), 1))),
                'attributes': self.generate_product_attributes(category.slug),
                'is_active': True,
            }
            
            try:
                product, created = Product.objects.get_or_create(
                    sku=product_data['sku'],
                    defaults=product_data
                )
                
                if created:
                    created_count += 1
                    # Create product variants
                    self.create_product_variants(product)
                    
                    if created_count % 10 == 0:
                        self.stdout.write(f'  Created {created_count} products...')
                        
            except Exception as e:
                self.stdout.write(f'  Error creating product {product_name}: {str(e)}')
        
        self.stdout.write(f'Created {created_count} products')

    def generate_product_description(self, name, category):
        """Generate a realistic product description."""
        descriptions = [
            f"High-quality {name.lower()} perfect for everyday use. ",
            f"Premium {name.lower()} designed with modern technology. ",
            f"Professional-grade {name.lower()} built to last. ",
            f"Stylish and functional {name.lower()} for {category.lower()} enthusiasts. ",
        ]
        
        features = [
            "Features advanced materials and construction.",
            "Includes warranty and customer support.",
            "Available in multiple colors and sizes.",
            "Eco-friendly and sustainable design.",
            "Easy to use with intuitive controls.",
            "Compact and portable design.",
        ]
        
        base_description = random.choice(descriptions)
        feature_list = random.sample(features, random.randint(2, 4))
        
        return base_description + " ".join(feature_list)

    def generate_product_attributes(self, category_slug):
        """Generate category-specific product attributes."""
        base_attributes = {
            'brand': random.choice(['Premium Brand', 'Quality Co.', 'Tech Solutions', 'Style Plus']),
            'warranty': f'{random.randint(1, 3)} years',
        }
        
        category_specific = {
            'smartphones': {
                'screen_size': f'{random.uniform(5.0, 7.0):.1f} inches',
                'storage': random.choice(['64GB', '128GB', '256GB', '512GB']),
                'color': random.choice(['Black', 'White', 'Blue', 'Red', 'Gold']),
            },
            'laptops': {
                'processor': random.choice(['Intel i5', 'Intel i7', 'AMD Ryzen 5', 'AMD Ryzen 7']),
                'memory': random.choice(['8GB', '16GB', '32GB']),
                'storage': random.choice(['256GB SSD', '512GB SSD', '1TB SSD']),
            },
            'clothing': {
                'size': random.choice(['XS', 'S', 'M', 'L', 'XL', 'XXL']),
                'color': random.choice(['Black', 'White', 'Blue', 'Red', 'Green', 'Gray']),
                'material': random.choice(['Cotton', 'Polyester', 'Wool', 'Silk', 'Linen']),
            },
            'shoes': {
                'size': random.choice(['6', '7', '8', '9', '10', '11', '12']),
                'color': random.choice(['Black', 'Brown', 'White', 'Blue', 'Red']),
                'material': random.choice(['Leather', 'Canvas', 'Synthetic', 'Mesh']),
            }
        }
        
        # Add category-specific attributes
        for category_key, attrs in category_specific.items():
            if category_key in category_slug:
                base_attributes.update(attrs)
                break
        
        return base_attributes

    def create_product_variants(self, product):
        """Create product variants for products that support them."""
        # Create 1-3 variants for some products
        if random.random() < 0.3:  # 30% of products get variants
            variant_count = random.randint(1, 3)
            
            for i in range(variant_count):
                variant_attributes = product.attributes.copy()
                
                # Modify some attributes for the variant
                if 'color' in variant_attributes:
                    colors = ['Black', 'White', 'Blue', 'Red', 'Green', 'Gray']
                    variant_attributes['color'] = random.choice(colors)
                
                if 'size' in variant_attributes:
                    sizes = ['S', 'M', 'L', 'XL'] if 'clothing' in product.category.slug else ['6', '7', '8', '9', '10']
                    variant_attributes['size'] = random.choice(sizes)
                
                price_variation = random.uniform(-50, 100)
                variant_price = max(product.price + Decimal(str(price_variation)), Decimal('1.00'))
                
                ProductVariant.objects.create(
                    product=product,
                    name=f'{product.name} - {variant_attributes.get("color", "Variant")} {i+1}',
                    sku=f'{product.sku}-V{i+1}',
                    price=variant_price,
                    stock=random.randint(0, 50),
                    attributes=variant_attributes,
                    is_active=True
                )

    def create_sample_reviews(self):
        """Create sample product reviews."""
        self.stdout.write('Creating sample reviews...')
        
        # Get or create sample users for reviews
        sample_users = []
        user_data = [
            ('reviewer1@example.com', 'Review', 'User1'),
            ('reviewer2@example.com', 'Review', 'User2'),
            ('reviewer3@example.com', 'Review', 'User3'),
        ]
        
        for email, first_name, last_name in user_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            sample_users.append(user)
        
        # Create reviews for random products
        products = Product.objects.all()[:20]  # Review first 20 products
        
        review_templates = [
            ("Great product!", "Really happy with this purchase. Quality is excellent and arrived quickly."),
            ("Good value", "Decent product for the price. Works as expected."),
            ("Excellent quality", "Outstanding quality and craftsmanship. Highly recommended!"),
            ("Not bad", "It's okay, does what it's supposed to do."),
            ("Amazing!", "This exceeded my expectations. Will definitely buy again."),
            ("Perfect", "Exactly what I was looking for. Perfect fit and finish."),
        ]
        
        review_count = 0
        for product in products:
            # Create 1-3 reviews per product
            num_reviews = random.randint(1, 3)
            selected_users = random.sample(sample_users, min(num_reviews, len(sample_users)))
            
            for user in selected_users:
                title, comment = random.choice(review_templates)
                rating = random.randint(3, 5)  # Mostly positive reviews
                
                ProductReview.objects.create(
                    product=product,
                    user=user,
                    rating=rating,
                    title=title,
                    review_text=comment,
                    is_verified_purchase=random.choice([True, False]),
                    is_approved=True
                )
                review_count += 1
        
        self.stdout.write(f'Created {review_count} sample reviews')